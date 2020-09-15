import scipy.io
import pymysql
import pandas as pd
import numpy as np
# dataFile = './data/new/xian_filtered.mat'
# data = scipy.io.loadmat(dataFile)
# print(data.keys())
# print(data['filtered_road_map_links'])
# print(data['filtered_road_map_ids'])


def parseTraces():
	dataFile = './data/new/1.mat'
	data = scipy.io.loadmat(dataFile)

	point = lambda x: [x[0], x[1]]
	print(data.keys())
	for line in data['alltrips']:
		trip_id, driver_id, timestamp, pose = line
		trip_id, driver_id = str(trip_id[0]), str(driver_id[0])
		timestamp = np.array([i[0] for i in timestamp])
		pose = np.array([point(i) for i in pose])
		trip_id = [trip_id]*len(pose)
		driver_id = [driver_id]*len(pose)
		probeID = np.array(list(range(len(pose))))
		df = pd.DataFrame({'probeID':probeID, 'car_id':driver_id, 'passenger_id':trip_id, 'timestamp':timestamp, 'longtitude':pose[:,1], 'latitude':pose[:,0]})
		df.to_csv('./data/traces/trace_{0}_{1}.csv'.format(driver_id[0][:5], trip_id[0][:5]), index=False, sep=',')

def parseMap():
	dataFile = './data/new/xian_filtered.mat'
	data = scipy.io.loadmat(dataFile)
	print(data['__header__'], data['__version__'], data['__globals__'])
	return
	point = lambda x: '{0}/{1}'.format(x[1], x[0])
	print(data.keys())
	links = data['filtered_road_map_links']
	ids = data['filtered_road_map_ids']
	# print(links)
	ps, ls = [], []
	for i, line in enumerate(links):
		pose = links[i]
		pose = '|'.join([point(i) for i in pose[0]])
		# print(pose)
		linkid = str(ids[i][0])
		ps, ls = ps+[pose], ls+[linkid]
	# print(ps, ls)
	df = pd.DataFrame({'linkPVID':np.array(ls), 'shapeInfo':np.array(ps)})
	df.to_csv('./data/map/map.csv', index=False, sep=',')

def toMySQL():
	for line in data['alltrips']:
		trip_id, driver_id, timestamp, pose = line
		trip_id, driver_id = str(trip_id[0]), str(driver_id[0])
		timestamp = '|'.join([str(i[0]) for i in timestamp])
		pose = '|'.join([point(i) for i in pose])
		query = "insert into traces(trip_id, driver_id, timestamp, pose) values ('{0}', '{1}', '{2}', '{3}')".format(trip_id, driver_id, timestamp, pose)
		cursor.execute(query)
		# print(query)
	db.commit()

parseMap()
# parseTraces()