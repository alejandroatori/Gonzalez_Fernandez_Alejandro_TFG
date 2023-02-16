/*
 *    Copyright (C) 2010 by RoboLab - University of Extremadura
 *
 *    This file is part of RoboComp
 *
 *    RoboComp is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU General Public License as published by
 *    the Free Software Foundation, either version 3 of the License, or
 *    (at your option) any later version.
 *
 *    RoboComp is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU General Public License for more details.
 *
 *    You should have received a copy of the GNU General Public License
 *    along with RoboComp.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "hokuyogenerichandler.h"

HokuyoGenericHandler::HokuyoGenericHandler(RoboCompLaser::LaserConfData &config, RoboCompGenericBase::GenericBasePrx base_prx, QObject *_parent) : GenericLaserHandler(base_prx, _parent)
{
	// Create the sampling timer
	timer = new QTimer(this );
	pm_timer = NULL;
	powerOn = false;
	setConfig(config);
}


HokuyoGenericHandler::~HokuyoGenericHandler()
{
 	timer->stop();
	disconnect ( timer );
	delete timer;
	pm_timer->stop();
	disconnect ( pm_timer );
	delete pm_timer;

	urg_disconnect(&urg);
	free(data);
}


void HokuyoGenericHandler::setConfig (RoboCompLaser::LaserConfData & config )
{
	confLaser = config;
	const char *device = confLaser.device.c_str();

	int ret; urg_parameter_t parameters;

	ret = urg_connect(&urg, device, 115200);
	if (ret < 0)
	{
		printf("%s: %d\n", __FILE__, __LINE__);
		urg_disconnect(&urg);
	}

	/* Get sensor parameter */
	ret = urg_parameters(&urg, &parameters);

	if (ret < 0)
	{
		urg_disconnect(&urg);
		qFatal("laserComp: Error getting config laser");
	}


	confLaser.minRange = parameters.distance_min_;
	confLaser.maxRange = parameters.distance_max_;

	confLaser.angleIni = urg_index2rad(&urg, parameters.area_min_);
	confLaser.angleRes = fabs(confLaser.angleIni - urg_index2rad(&urg, parameters.area_min_ + 1));

	confLaser.maxMeasures = (confLaser.endRange - confLaser.iniRange)/confLaser.cluster;

	std::cout << "device: " << confLaser.device << std::endl;
	std::cout << "driver: " << confLaser.driver << std::endl;

	std::cout << "angleIni: " << confLaser.angleIni*180/M_PI << std::endl;
	std::cout << "angleRes: " << confLaser.angleRes << std::endl;

	std::cout << "maxRange: " << confLaser.maxRange << std::endl;
	std::cout << "minRange: " << confLaser.minRange << std::endl;

	std::cout << "endRange: " << confLaser.endRange << std::endl; //confLaser.endRange << std::endl;
	std::cout << "iniRange: " << confLaser.iniRange << std::endl;

	std::cout << "cluster: " << confLaser.cluster << std::endl;
	std::cout << "maxMeasures: " << confLaser.maxMeasures << std::endl;

	urg_disconnect(&urg);

	wdataR.resize( confLaser.maxMeasures );
	wdataW.resize( confLaser.maxMeasures );
}

bool HokuyoGenericHandler::open()
{
	// Open and initialize the device

	/* Connection */
	const char *device = confLaser.device.c_str();
	int ret = urg_connect(&urg, device, 115200);
	if (ret < 0)
	{
		urg_disconnect(&urg);
		exit(1);
	}

	/* Reserve for reception data */
	data_max = urg_dataMax(&urg);


	data = (long*)malloc(sizeof(long) * data_max);
	if (data == NULL)
	{
		perror("malloc");
		exit(1);
	}

	printf("Connection opened OK.\n");
	return true;
}

bool HokuyoGenericHandler::isPowerOn()
{
	return powerOn;
}

bool HokuyoGenericHandler::poweronLaser()
{
	return true;
}

void HokuyoGenericHandler::poweroffLaser()
{

}

bool HokuyoGenericHandler::setLaserPowerState ( bool state )
{
	return true;
}

bool HokuyoGenericHandler::readLaserData()
{
	powerOn = true;

	int min_length = 0;
	int max_length = 0;


	/* Request for GD data */
	int ret;
	ret = urg_requestData(&urg, URG_GD, URG_FIRST, URG_LAST);
	if (ret < 0)
	{
		urg_disconnect(&urg);
		exit(1);
	}

	/* Reception */
	int n;
	n = urg_receiveData(&urg, data, data_max);
	if (n < 0)
	{
		urg_disconnect(&urg);
		printf("urg_disconnect\n");
		return false;
	}
	else
	{
		/* Output as 2 dimensional data */
		/* Consider front of URG as positive direction of X axis */
		min_length = urg_minDistance(&urg);
		max_length = urg_maxDistance(&urg);

		int i = 0;

		for( int k = confLaser.iniRange; k < confLaser.endRange; ++k)
		{
//			int x, y;
			long length = data[k];


			/* Neglect out of range values */
			if ((length <= min_length) || (length >= max_length))
			{
				continue;
			}

//			x = (int)(length * cos(urg_index2rad(&urg, k)));
//			y = (int)(length * sin(urg_index2rad(&urg, k)));
			if ( k % confLaser.cluster == 0)
			{
				wdataW[i].dist = length;
				wdataW[i].angle =  -urg_index2rad(&urg, k);
				i++;
			}
		}


		//Double buffering
		laserMutex.lock();
		wdataW.swap(wdataR);
		laserMutex.unlock();
		return true;
	}
}

int HokuyoGenericHandler::SiguienteNoNulo(RoboCompLaser::TLaserData & laserData,int pos,int aStart,int aEnd)
{
	return ( 0 );
}


RoboCompLaser::TLaserData HokuyoGenericHandler::getNewData()
{
	QMutexLocker mlocker(&laserMutex);
	return wdataR;
}

RoboCompLaser::LaserConfData HokuyoGenericHandler::getLaserConf()
{
	return confLaser;
}


///Check Laser use for powersaving
void HokuyoGenericHandler::checkLaserUse()
{
	if ( last_use.elapsed() > LASER_TIMEOUT )
		poweroffLaser();
}
///Thread main loop
void HokuyoGenericHandler::run()
{
	for (;;)
	{
		//last_use.restart();
		if (readLaserData()==false)
		{
			std::cout << "Error reading laser (generic)" << std::endl;
			usleep(500000);
		}
	}
}

