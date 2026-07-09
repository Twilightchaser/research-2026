const MQTT_Product_Id = "YOUR_PRODUCT_ID";
const MQTT_Device_Name = "YOUR_DEVICE_NAME";

const MQTT_GET_URL = "https://iot-api.heclouds.com/thingmodel/query-device-property?product_id=" + MQTT_Product_Id + "&device_name=" + MQTT_Device_Name;
const MQTT_POST_URL = "https://iot-api.heclouds.com/thingmodel/set-device-desired-property";
const MQTT_Authorization = "YOUR_ONENET_AUTHORIZATION";
const REQUEST_TIMEOUT = 5000;
const REALTIME_POLL_INTERVAL = 1000;
const HISTORY_LIMIT = 12;
const HISTORY_STORAGE_KEY = "elder_pose_history";
const FALL_ALERT_INTERVAL = 10000;
const SITTING_ALERT_INTERVAL = 30000;
const DEMO_MODE = false;
const DEMO_VALUES = [0, 1, 2];

const APP_Name = "老年人姿态识别系统";
const Val1_Name = "当前姿态";

const util = require("../../utils/util.js");
const aiRisk = require("../../utils/aiRisk.js");

function getStatusInfo(value) {
  var code = Number(value);

  if (code === 0) {
    return {
      statusText: "状态正常",
      statusClass: "normal",
      statusIcon: "✓",
      statusDesc: "当前姿态平稳，未检测到异常风险。",
      riskText: "风险等级：低",
      careTag: "安心",
      careAdvice: "保持当前监测状态即可，建议家属定时查看同步时间和设备连接情况。"
    };
  }

  if (code === 1) {
    return {
      statusText: "疑似跌倒",
      statusClass: "fall",
      statusIcon: "!",
      statusDesc: "检测到高风险姿态变化，请尽快确认老人安全。",
      riskText: "风险等级：高",
      careTag: "立即关注",
      careAdvice: "请马上电话联系或到现场查看；若无法确认情况，建议及时通知家属或护理人员。"
    };
  }

  if (code === 2) {
    return {
      statusText: "久坐提醒",
      statusClass: "sitting",
      statusIcon: "i",
      statusDesc: "检测到长时间坐姿，建议适度起身活动。",
      riskText: "风险等级：中",
      careTag: "需要活动",
      careAdvice: "可以提醒老人缓慢起身、活动肩颈和下肢，避免突然站立导致眩晕。"
    };
  }

  return {
    statusText: "状态未知",
    statusClass: "unknown",
    statusIcon: "?",
    statusDesc: "暂未识别到有效姿态，请检查设备佩戴或网络连接。",
    riskText: "风险等级：待确认",
    careTag: "待同步",
    careAdvice: "请确认传感器电源、佩戴位置和网络连接是否正常。"
  };
}

function getPropertyValue(list, identifier, fallback) {
  var item = list.find(function (property) {
    return property.identifier === identifier;
  });

  return item && item.value !== undefined ? item.value : fallback;
}

function toFixedNumber(value, fallback) {
  var number = Number(value);

  if (isNaN(number)) {
    return fallback;
  }

  return number.toFixed(0);
}

function buildHistoryStats(records) {
  var stats = {
    total: records.length,
    normal: 0,
    fall: 0,
    sitting: 0,
    latestAlert: "暂无异常"
  };

  records.forEach(function (record) {
    if (record.statusClass === "normal") {
      stats.normal++;
    } else if (record.statusClass === "fall") {
      stats.fall++;
    } else if (record.statusClass === "sitting") {
      stats.sitting++;
    }
  });

  var latestAlert = records.find(function (record) {
    return record.statusClass === "fall" || record.statusClass === "sitting";
  });

  if (latestAlert) {
    stats.latestAlert = latestAlert.statusText + " · " + latestAlert.time;
  }

  return stats;
}

Page({
  data: {
    time: "",
    Val1_Num: 0,
    Val2_Num: 0,
    Val3_Num: 0,
    Val4_Num: 0,
    Val5_Num: 0,
    Val6_Num: 0,
    Val7_Num: 0,
    Val8_Num: 0,
    historyRecords: [],
    historyStats: {
      total: 0,
      normal: 0,
      fall: 0,
      sitting: 0,
      latestAlert: "暂无异常"
    },
    isRefreshing: false,
    alertHandled: false,
    val1name: Val1_Name,
    statusText: "状态正常",
    statusClass: "normal",
    statusIcon: "✓",
    statusDesc: "当前姿态平稳，未检测到异常风险。",
    riskText: "风险等级：低",
    careTag: "安心",
    careAdvice: "保持当前监测状态即可，建议家属定时查看同步时间和设备连接情况。",
    aiRisk: aiRisk.evaluate({
      statusCode: 0,
      angle: 90,
      still: 0
    }, [])
  },

  updateStatus: function (value) {
    var nextRisk = aiRisk.evaluate({
      statusCode: value,
      angle: this.data.Val2_Num,
      still: this.data.Val3_Num
    }, this.data.historyRecords);

    this.setData(Object.assign(getStatusInfo(value), {
      aiRisk: nextRisk
    }));
  },

  triggerLocalAlert: function (val1) {
    var code = Number(val1);
    var now = Date.now();

    if (code === 1 && (!this.lastFallAlertTime || now - this.lastFallAlertTime > FALL_ALERT_INTERVAL)) {
      this.lastFallAlertTime = now;
      this.setData({
        alertHandled: false
      });
      wx.vibrateLong();
      wx.showModal({
        title: "疑似跌倒告警",
        content: "检测到高风险姿态变化，请尽快确认老人安全。",
        confirmText: "已知晓",
        showCancel: false
      });
    }

    if (code === 2 && (!this.lastSittingAlertTime || now - this.lastSittingAlertTime > SITTING_ALERT_INTERVAL)) {
      this.lastSittingAlertTime = now;
      wx.vibrateShort({
        type: "heavy"
      });
    }
  },

  notifyFamily: function () {
    wx.showModal({
      title: "通知家属",
      content: "已生成异常提醒：当前状态为“" + this.data.statusText + "”。演示场景下使用弹窗模拟短信/电话通知。",
      confirmText: "知道了",
      showCancel: false
    });
  },

  confirmHandled: function () {
    this.setData({
      alertHandled: true
    });
    wx.showToast({
      title: "已确认处理",
      icon: "success",
      duration: 900
    });
  },

  addHistoryRecord: function (val1, val2, val3) {
    var statusInfo = getStatusInfo(val1);
    var record = {
      id: Date.now() + "-" + Math.floor(Math.random() * 1000),
      time: util.formatTime(new Date()),
      statusText: statusInfo.statusText,
      statusClass: statusInfo.statusClass,
      angle: toFixedNumber(val2, "--"),
      still: toFixedNumber(val3, "0")
    };
    var records = [record].concat(this.data.historyRecords).slice(0, HISTORY_LIMIT);

    this.setData({
      historyRecords: records,
      historyStats: buildHistoryStats(records),
      aiRisk: aiRisk.evaluate({
        statusCode: val1,
        angle: val2,
        still: val3
      }, records)
    });
    wx.setStorageSync(HISTORY_STORAGE_KEY, records);
  },

  updateDemoStatus: function () {
    this.demoIndex = this.demoIndex === undefined ? 0 : (this.demoIndex + 1) % DEMO_VALUES.length;
    var val1 = DEMO_VALUES[this.demoIndex];
    var val2 = val1 === 1 ? 35 : 96;
    var val3 = val1 === 2 ? 25 : 0;

    this.setData(Object.assign({
      Val1_Num: val1,
      Val2_Num: val2,
      Val3_Num: val3
    }, getStatusInfo(val1)));
    this.triggerLocalAlert(val1);
    this.addHistoryRecord(val1, val2, val3);
  },

  refreshNow: function () {
    this.getinfo(true);
  },

  clearHistory: function () {
    this.setData({
      historyRecords: [],
      historyStats: buildHistoryStats([]),
      aiRisk: aiRisk.evaluate({
        statusCode: this.data.Val1_Num,
        angle: this.data.Val2_Num,
        still: this.data.Val3_Num
      }, [])
    });
    wx.removeStorageSync(HISTORY_STORAGE_KEY);
  },

  openHistory: function () {
    wx.setStorageSync(HISTORY_STORAGE_KEY, this.data.historyRecords);
    wx.navigateTo({
      url: "../history/history",
      fail: function (err) {
        console.error("Open history page failed", err);
        wx.showToast({
          title: "历史页打开失败",
          icon: "none"
        });
      }
    });
  },

  getinfo: function (force) {
    var that = this;

    if (DEMO_MODE) {
      this.updateDemoStatus();
      return;
    }

    if (this.isFetching && !force) {
      return;
    }

    this.isFetching = true;
    this.setData({
      isRefreshing: !!force
    });

    wx.request({
      url: MQTT_GET_URL,
      header: {
        "authorization": MQTT_Authorization
      },
      method: "GET",
      timeout: REQUEST_TIMEOUT,
      success: function (res) {
        var list = res.data && res.data.data ? res.data.data : [];
        var val1 = getPropertyValue(list, "Val1", that.data.Val1_Num);
        var nextData = {
          Val1_Num: val1,
          Val2_Num: getPropertyValue(list, "Val2", that.data.Val2_Num),
          Val3_Num: getPropertyValue(list, "Val3", that.data.Val3_Num),
          Val4_Num: getPropertyValue(list, "Val4", that.data.Val4_Num),
          Val5_Num: getPropertyValue(list, "Val5", that.data.Val5_Num),
          Val6_Num: getPropertyValue(list, "Val6", that.data.Val6_Num),
          Val7_Num: getPropertyValue(list, "Val7", that.data.Val7_Num),
          Val8_Num: getPropertyValue(list, "Val8", that.data.Val8_Num)
        };

        that.setData(Object.assign(nextData, getStatusInfo(val1)));
        that.triggerLocalAlert(val1);
        that.addHistoryRecord(val1, nextData.Val2_Num, nextData.Val3_Num);
        if (force) {
          wx.showToast({
            title: "已刷新",
            icon: "success",
            duration: 800
          });
        }
      },
      fail: function (err) {
        console.error("OneNET property request failed", err);
        if (force) {
          wx.showToast({
            title: "刷新超时",
            icon: "none"
          });
        }
      },
      complete: function () {
        that.isFetching = false;
        that.setData({
          isRefreshing: false
        });
      }
    });
  },

  sendKey: function (keyValue) {
    wx.request({
      url: MQTT_POST_URL,
      method: "POST",
      header: {
        "authorization": MQTT_Authorization
      },
      timeout: REQUEST_TIMEOUT,
      data: {
        "product_id": MQTT_Product_Id,
        "device_name": MQTT_Device_Name,
        "params": {
          "Key_Val": keyValue
        }
      }
    });
  },

  kai: function () {
    this.sendKey(1);
  },

  guan: function () {
    this.sendKey(0);
  },

  K1: function () {
    this.sendKey(1);
  },

  K2: function () {
    this.sendKey(2);
  },

  K3: function () {
    this.sendKey(3);
  },

  K4: function () {
    this.sendKey(4);
  },

  K5: function () {
    this.sendKey(5);
  },

  K6: function () {
    this.sendKey(6);
  },

  K7: function () {
    this.sendKey(7);
  },

  K8: function () {
    this.sendKey(8);
  },

  K9: function () {
    this.sendKey(9);
  },

  onLoad: function () {
    var that = this;

    wx.setNavigationBarTitle({
      title: APP_Name
    });

    wx.setNavigationBarColor({
      frontColor: "#000000",
      backgroundColor: "#eef7f6"
    });

    this.updateStatus(this.data.Val1_Num);
    var storedRecords = wx.getStorageSync(HISTORY_STORAGE_KEY) || [];
    this.setData({
      time: util.formatTime(new Date()),
      historyRecords: storedRecords,
      historyStats: buildHistoryStats(storedRecords),
      aiRisk: aiRisk.evaluate({
        statusCode: this.data.Val1_Num,
        angle: this.data.Val2_Num,
        still: this.data.Val3_Num
      }, storedRecords)
    });
    this.getinfo();

    this.dataTimer = setInterval(function () {
      that.getinfo();
    }, DEMO_MODE ? 5000 : REALTIME_POLL_INTERVAL);

    this.clockTimer = setInterval(function () {
      that.setData({
        time: util.formatTime(new Date())
      });
    }, 1000);
  },

  onUnload: function () {
    if (this.dataTimer) {
      clearInterval(this.dataTimer);
    }

    if (this.clockTimer) {
      clearInterval(this.clockTimer);
    }
  }
});
