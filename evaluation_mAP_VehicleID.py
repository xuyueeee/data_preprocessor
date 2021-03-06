#coding:utf-8

from __future__ import division
import numpy as np
import random
import argparse
import scipy.io as sio
import os

parser = argparse.ArgumentParser(description="calculate mAP for VehicleID dataset using specific split strategy.")
parser.add_argument('-cn','--class_num', type=int, help='class number of test set. options:800, 1600, 2400.')
parser.add_argument('-gn','--group_num', type=int, help='group number of evaluation to calculate average value. no less than 1.')
parser.add_argument('-f','--feature', type=str, help='path of the .mat feature file.') 
parser.add_argument('-l', '--imageList', type=str, help='path of the image list.')
args = parser.parse_args()

def compare1(a, b):
    if a[1][1] - a[1][0] > b[1][1] - b[1][0]:
        return -1
    elif a[1][1]  - a[1][0] < b[1][1] - b[1][0]:
        return 1
    else:
        if a[1][0] < b[1][0]:
            return -1
        else:
            return 1
        

result = []
for iterCount in range(0, args.group_num):
    print ("start iter {:d}".format(iterCount+1))
    print "split gallery/probe set ..."         
    print "split gallery/probe set ..." 
    testFile = open(os.path.join(args.imageList, 'test' + str(args.class_num) + "_all.lst"))
    cars = {}
    i=0
    lines = testFile.readlines()
    for i in range(len(lines)):
        line = lines[i]
        lineList = line.split()
        # 分别记录某ID的车第一次出现和最后一次出现在列表中的位置
        if cars.has_key(lineList[1]):
            cars[lineList[1]][1] = i
        else:
            cars[lineList[1]] = np.zeros(shape=(2), dtype=np.int32)
            cars[lineList[1]][0] = i
    carsList = cars.items()
    # sort by image number of each class.
    carsList.sort(compare1)


    j = 0
    probeIndice = []
    galleryIndice = []
    galleryCount = []
    # 之前的理解好像有问题。。
    # for car in carsList:
    #     if car[1][1] - car[1][0] + 1 <= 6:
    #         continue
    #     galleryIndexArr = []
    #     # there are 6 images in gallery set per class
    #     # other images are throw to probe set
    #     while len(galleryIndexArr) < car[1][1] - car[1][0]:
    #         galleryIndex = random.randint(car[1][0], car[1][1])
    #         if not galleryIndex in galleryIndexArr:
    #             galleryIndexArr.append(galleryIndex)
            
    #     tmpCount = 0
    #     for i in range(car[1][0], car[1][1]+1):
    #         if i not in galleryIndexArr:
    #             probeIndice.append(tuple([i, car[0]]))
    #         else:
    #             galleryIndice.append(tuple([i,car[0]]))
    #             tmpCount += 1
    #     galleryCount.append(tmpCount)

    for car in carsList:
        probeIndex = random.randint(car[1][0], car[1][1])
        probeIndice.append(tuple([probeIndex, car[0]]))
        #if car[1][1] - car[1][0] >= 6:
        for i in range(car[1][0], car[1][1]+1):
            if i != probeIndex:
                galleryIndice.append(tuple([i, car[0]]))
        if car[1][1] - car[1][0] < 6:
            for i in range(0, 6-(car[1][1] - car[1][0])):
                while True:
                    galleryIndex =  random.randint(car[1][0], car[1][1])
                    if galleryIndex != probeIndex:
                        galleryIndice.append(tuple([galleryIndex, car[0]]))
                        break
            galleryCount.append(6)
        else:
            galleryCount.append(car[1][1] - car[1][0])


    print 'calculate similarity matrix ...'
    features = sio.loadmat(args.feature)['feature']
    #features = sio.loadmat('../evaluation/VehicleID/0630_1.2/feature2400.mat')['feature']
    feature_query = np.zeros(shape=(len(probeIndice), features.shape[1]))
    feature_ref = np.zeros(shape=(len(galleryIndice), features.shape[1]))
    for i in range(0, len(probeIndice)):
        feature_query[i,...] = features[probeIndice[i][0]]
    for i in range(0, len(galleryIndice)):
        feature_ref[i, ...] = features[galleryIndice[i][0]]
    similar_cosine = np.zeros(shape=(feature_query.shape[0], feature_ref.shape[0]))

    #将特征向量归一化
    L2_query = np.zeros(shape=(feature_query.shape[0]))
    #print feature_query.shape
    L2_ref = np.zeros(shape=(feature_ref.shape[0]))
    for i in range(0, len(feature_query)):
        L2_query[i] = np.linalg.norm(feature_query[i,:])
    for i in range(0, len(feature_ref)):
        L2_ref[i] = np.linalg.norm(feature_ref[i,:])    
        
    #计算query中每个元素和ref中每个元素的距离    
    for i in range(0, len(feature_query)):
        #if i % 100 == 0:
        #   print i
        for j in range(0, len(feature_ref)):
            v1 = feature_query[i,:]
            v2 = feature_ref[j,:]
            similar_cosine[i,j] = np.dot(v1,v2) / (L2_query[i] * L2_ref[j])

    #对query中的每个元素，将它与ref中每个元素的相似度按照从大到小排序
    label_sorted_cosine = np.zeros(shape=np.shape(similar_cosine), dtype='int64')
    for i in range(0, similar_cosine.shape[0]):
        label_sorted_cosine[i,:] = np.argsort(-similar_cosine[i])



    print "calculate mAP ..."
    mAP = 0
    for i in range(len(probeIndice)):
        ap = 0
        gtCount = galleryCount[i]
        gtCur = 0
        for j in range(len(galleryIndice)):
            if galleryIndice[label_sorted_cosine[i][j]][1] == probeIndice[i][1]:
                #print 'a'
                gtCur += 1
                ap += gtCur / (j+1)
                if gtCur == gtCount:
                    break
        #print ap
        ap /= gtCount
        
        mAP += ap
    mAP /= len(probeIndice)
    print ("mAP of iter{:d}:{:f}".format(iterCount+1, mAP))
    result.append(mAP)

mAP = 0
for i in range(0, args.group_num):
    mAP += result[i]
mAP /= args.group_num

print ("mAP(avg):{:f}".format(mAP))


