import numpy as np
import pandas as pd
import os
from shapely.geometry import Point
from shapely.geometry import LineString
import pandas as pd
from shapely.ops import nearest_points
from shapely import wkt
import math
from tqdm import tqdm
import utm
import geopandas
from shapely import wkt
from pointwise import *

info2wkt = lambda info: 'LINESTRING ({0})'.format(', '.join(["{0} {1}".format(node.split('/')[1], node.split('/')[0]) for node in str(info).split('|')]))
shape2utm = lambda shape: [(utm.from_latlon(c[1], c[0])[0], utm.from_latlon(c[1], c[0])[1]) for c in shape.coords]
row2point = lambda row:  "POINT ({0} {1})".format(str(row["longitude"]), str(row["latitude"]))
caleast = lambda row: utm.from_latlon(row["latitude"], row["longitude"])[0]
calnorth = lambda row: utm.from_latlon(row["latitude"], row["longitude"])[1]

def parseGPS(car_idx, idx):
	with open('./data/points/gps_20161001') as f:
		all_info = f.readlines()
		res = []
		for line in all_info:
			if line.split(',')[0] == car_idx:
				res.append(line.strip())
		res = np.array(res)
		np.save('./data/clean/cars/car_{0}.npy'.format(idx), res)

def trvGPS():
	with open('./data/points/gps_20161001') as f:
		car_idxs = set()
		lines = f.readlines()
		pbar = tqdm(len(lines))
		for line in lines:
			car_idxs.add(line.split(',')[0])
			pbar.update()
		pbar.close()

		idx = 0
		pbar = tqdm(len(car_idxs))
		for car_idx in car_idxs:
			res = []
			for line in lines:
				if line.split(',')[0] == car_idx:
					res.append(line.strip())
			res = np.array(res)
			np.save('./data/clean/cars/car_{0}.npy'.format(idx), res)
			idx += 1
			pbar.update()

def parseLinks():
	path = './data/links/'
	files = os.listdir(path)
	files = [i for i in files if i.split('.')[-1]=='nodes']
	files.sort(key=lambda x:(int(x.split('.')[0]), int(x.split('.')[1])))
	shape, res = [], []
	idx = int(files[0].split('.')[0])
	for file in files:
		print(file)
		cur = int(file.split('.')[0])
		if cur != idx:
			res.append([idx, '|'.join(shape)])
			idx = cur
			shape = []
		with open(path+file) as sublinks:
			sublink = sublinks.readlines()
			for line in sublink:
				shape.append(line.strip().replace(' ', '/'))
	# print(nodes)
	if shape:
		res.append([idx, '|'.join(shape)])
	np.save('./data/clean/links_combine.npy', np.array(res))

def getPoints():
	points = np.load('./data/points/car_0.npy')
	points[i] = np.array(list(map()))
	return points

def makeCSV():
	car = np.load('./data/clean/car_0.npy')
	links = np.load('./data/clean/links_combine.npy')
	new_car = []
	probe = 0
	user_idx = 0
	users = {}
	for i in range(car.shape[0]):
		line = car[i].strip().split(',')
		# print(line)
		if line[1] in users:
			new_car.append([probe, 0, users[line[1]], float(line[2]), float(line[3]), float(line[4])])
			probe += 1
		else:
			users[line[1]] = user_idx
			user_idx += 1
			probe += 1
			new_car.append([probe, 0, users[line[1]], float(line[2]), float(line[3]), float(line[4])])
	car = pd.DataFrame(new_car, columns = ['probeID', 'car_id', 'passenger_id', 'timestamp', 'longitude', 'latitude'])
	car.to_csv('./data/clean/car_0.csv')
	# links = pd.DataFrame(links, columns = ['link_id', 'sublink_id', 'linkPVID', 'shapeInfo'])
	links = pd.DataFrame(links, columns = ['link_id','shapeInfo'])
	links.to_csv('./data/clean/links_combine.csv')

def transPoints(source='./data/clena/car_0.csv', target='./data/clean/cars_0_NE.csv'):
	names = ['probeID', 'car_id', 'passenger_id', 'timestamp', 'longitude', 'latitude']
	data_probes = pd.read_csv(source, header=0, names=names)
	# print(data_probes['latitude'])
	data_probes.index.name = 'car_id'
	data_probes["shape"] = data_probes.apply(row2point, axis=1).apply(wkt.loads)
	data_probes["easting"] = data_probes.apply(caleast, axis=1)
	data_probes["northing"] = data_probes.apply(calnorth, axis=1)
	data_probes = geopandas.GeoDataFrame(data_probes, geometry='shape')
	data_probes.to_csv(target)

def transLinks(source='./data/clean/links_combine.csv', target='./data/clean/links_combine_NE.csv'):
    # names = ['link_id', 'sublink_id', 'linkPVID', 'shapeInfo']
    names = ['linkPVID','shapeInfo']
    data_links = pd.read_csv(source, header=0, names=names)
    # data_links.index.name = 'linkPVID'
    data_links['shape'] = data_links["shapeInfo"].apply(info2wkt).apply(wkt.loads)
    geo_data_links = geopandas.GeoDataFrame(data_links, geometry='shape')
    data_links['utms'] = geo_data_links["shape"].apply(shape2utm)
    data_links.to_csv(target)

def loadCleanData(datatype, root):
    if datatype is 'links':
        data_links = pd.read_csv(root+'/links.csv')
        data_links['shape'] = data_links['shape'].apply(wkt.loads)
        data_links = geopandas.GeoDataFrame(data_links, geometry='shape')
        return data_links
    elif datatype is 'points':
        data_probes = pd.read_csv(root+'/points.csv')
        data_probes['shape'] = data_probes['shape'].apply(wkt.loads)
        data_probes = geopandas.GeoDataFrame(data_probes, geometry='shape')
        return data_probes
    elif datatype is 'match':
        data_match = pd.read_csv(root+'/match.csv')
        # data_match['shape'] = data_match['shape'].apply(wkt.loads)
        # data_match = geopandas.GeoDataFrame(data_match, geometry='shape')
        return data_match

def visualize(links, match):
	from matplotlib import pyplot as plt
	tmp = []
	plt.cla()
	m, M = float('-Inf'), float('Inf')

	link_idx = set()
	tmp = []
	for i, row in match.iterrows():
		PVID = row['linkPVID']
		combine_id = '{0}_{1}'.format(str(row['car_id.1'])[:5], str(row['passenger_id'])[:5])
		distance = row['distance']
		link_idx.add(PVID)
		if distance < M:
			# x, y = row['easting'], row['northing']
			x, y = list(map(float, row['projection_NE'][8:-1].split(' ')))
			print(x, y)
			plt.scatter(x, y, color=((PVID%150+50)/256, (PVID%120+80)/256, (PVID%100+100)/256), alpha=0.5, s=0.5)
	for i, row in links.iterrows():
		PVID = row['linkPVID']
		if True:
			xys = []
			pts = [i.split(',')[::-1] for i in row['utms'][2:-2].split('), (')]
			# print(pts)
			for p in pts:
				x, y = float(p[0]), float(p[1])
				if not [x, y] in xys:
					xys.append([x, y])
				else:
					pass
			xys = np.array(xys)
			x, y = xys[:,1], xys[:,0]
			plt.plot(x, y, color=((PVID%150+50)/256, (PVID%120+80)/256, (PVID%100+100)/256), lw=0.3)
			plt.axis('equal')
	plt.show()
	plt.savefig('./data/match/fig_{0}'.format(combine_id), dpi=1000)

def score(match):
	scr = 0
	cnt = 0
	threshold = 20
	for i, row in match.iterrows():
		distance = row['distance']
		if distance < 20:
			scr += distance
			cnt += 1
	if i and cnt:
		return scr, i, cnt/i, scr/cnt
	else:
		return float('-Inf'), i, 0, float('-Inf')

def collect(source, target):
	files = [source+'/'+i for i in os.listdir(source)][:]
	data = []
	for file in files:
		arr = np.load(file, allow_pickle=True)
		data.append(arr)
	data = np.array(data)
	import scipy.io
	scipy.io.savemat(target, {'alltrips_clean':data})

if __name__ == '__main__':
	# import utm
	# print(utm.to_latlon(313349.9020869538, 3794977.7993340287, 49, 'U'))
	# quit()

	# trvGPS()

	# parse data
	# parseGPS()
	# getPoints()
	# parseLinks()

	# make pandas
	# makeCSV()
	# quit()

	# root = './data/csv'
	# links = loadCleanData(datatype='links', root=root)
	# match = loadCleanData(datatype='match', root=root)
	# visualize(links, match)
	# quit()


	import shutil
	files = ['./data/traces/'+i for i in os.listdir('./data/traces')][:]
	nums = 10
	pbar = tqdm(total=nums)
	for i in range(nums):
		pbar.update()
		# print('{0}/{1} ({2}%) Done. Matching: {3}'.format(i, nums, round(i*100/nums, 2), files[i]))
		# shutil.copyfile(files[i], './data/csv/trace.csv')

		transLinks(source='./data/csv/map.csv', target='./data/csv/links.csv')
		# transPoints(source='./data/csv/trace.csv', target='./data/csv/points.csv')
		transPoints(source=files[i], target='./data/csv/points.csv')

		root = './data/csv'
		links = loadCleanData(datatype='links', root=root)
		points = loadCleanData(datatype='points', root=root)
		point_wise_match(links, points, 50000,'./data/csv/match.csv')
		match = loadCleanData(datatype='match', root=root)
		# print(score(match))
		scr, num, prop, avg = score(match)
		# print(scr, num, prop, avg)
		if prop > 0.95 and avg < 10:
			pose = np.array(match[['latitude', 'longitude']])
			timestamp = np.array(match[['timestamp']]).astype(np.float64)
			trip_id, driver_id = match['passenger_id'][0], match['car_id.1'][0]
			link_id, projection = np.array(match[['linkPVID']]).astype(np.uint), np.array(match[['projection_lat', 'projection_lon']])
			# print(projection)
			cur = np.array([trip_id, driver_id, timestamp, pose, link_id, projection])
			np.save('./data/collect/collect_095/cur_{0}.npy'.format(i), cur)
			# print(trip_id, driver_id, pose, timestamp)
			# cur_data.append(np.array([trip_id, driver_id, timestamp, pose]))
			# print(cur_data)
		collect('./data/collect/collect_095', './data/new/1_clean.mat')