def getlocation(payload):
    MAXPAYLOADLEN = 82
    MINSNR = 3.0
    MINRSSI = -85
    MINANGLE = 20
    UNDERANGLE = 5
    try:
        strstart = 16
        payload = payload.strip()
        payloadlen = len(payload)
        if (payloadlen == MAXPAYLOADLEN):
            customdatalen = 36 + 14
        else:
            payloadlen = -1

        if (payloadlen != -1) and (payload.find('AOA=') != -1):
            macid = payload[strstart - 2:strstart] + payload[strstart - 4:strstart - 2] + payload[strstart - 6:strstart - 4] + payload[strstart - 8:strstart - 6] + payload[strstart - 10:strstart - 8] + payload[strstart - 12:strstart-10]
            custumdata = payload[strstart:strstart+customdatalen]
            rssi = (int(payload[strstart + customdatalen + 2:strstart + customdatalen + 4] + payload[strstart + customdatalen:strstart + customdatalen + 2], 16) - 256) * 0.5
            snr = int(payload[strstart + customdatalen + 6:strstart + customdatalen + 8] + payload[strstart + customdatalen + 4:strstart + customdatalen + 6], 16) / 10
            azimuth = int(payload[strstart + customdatalen + 10:strstart + customdatalen + 12] + payload[strstart + customdatalen + 8:strstart + customdatalen + 10], 16) * 0.5
            elevation = int(payload[strstart + customdatalen + 14:strstart + customdatalen + 16] + payload[strstart + customdatalen + 12:strstart + customdatalen + 14], 16) * 0.5
            if azimuth != 0:
                azimuth = 360 - azimuth
            elevation = 90 - elevation
            if elevation > 90 - MINANGLE:
                return
            if rssi < MINRSSI:
                return
            if (payloadlen == MAXPAYLOADLEN):
                if (elevation > UNDERANGLE):
                    if snr < MINSNR:
                        return
        #############################################################
        #获取数据后进行处理
        #macid MAC地址
        #custumdata 用户数据
        #rssi 信号强度
        #snr 信噪比
        #azimuth方位角
        #elevation倾角

    except Exception:
        loggererr.error('Error:%s happens when getting location!',str(Exception))
