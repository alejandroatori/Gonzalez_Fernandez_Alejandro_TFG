//******************************************************************
// 
//  Generated by RoboCompDSL
//  
//  File name: YoloObjects.ice
//  Source: YoloObjects.idsl
//
//******************************************************************
#ifndef ROBOCOMPYOLOOBJECTS_ICE
#define ROBOCOMPYOLOOBJECTS_ICE
#include <CameraRGBDSimple.ice>
module RoboCompYoloObjects
{
	struct TBox
	{
		int id;
		int type;
		int left;
		int top;
		int right;
		int bot;
		float prob;
	};
	sequence <TBox> TObjects;
	sequence <string> TObjectNames;
	struct TKeyPoint
	{
		float x;
		float y;
		float z;
		int i;
		int j;
		float score;
	};
	dictionary <int, TKeyPoint> TJoints;
	struct TPerson
	{
		int id;
		int box;
		TJoints joints;
	};
	sequence <TPerson> TPeople;
	dictionary <int, string> TJointNames;
	struct TConnection
	{
		int first;
		int second;
	};
	sequence <TConnection> TConnections;
	struct TJointData
	{
		TJointNames jointNames;
		TConnections connections;
	};
	struct TData
	{
		TObjects objects;
		TPeople people;
		int timestamp;
	};
	interface YoloObjects
	{
		RoboCompCameraRGBDSimple::TImage getImage ();
		TJointData getYoloJointData ();
		TObjectNames getYoloObjectNames ();
		TData getYoloObjects ();
	};
};

#endif
