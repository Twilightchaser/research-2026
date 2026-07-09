const HISTORY_STORAGE_KEY = "elder_pose_history";
const aiRisk = require("../../utils/aiRisk.js");

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
    historyRecords: [],
    historyStats: buildHistoryStats([]),
    historyRisk: aiRisk.evaluate({
      statusCode: 0,
      angle: 90,
      still: 0
    }, [])
  },

  loadHistory: function () {
    var records = wx.getStorageSync(HISTORY_STORAGE_KEY) || [];
    var latest = records[0] || {};

    this.setData({
      historyRecords: records,
      historyStats: buildHistoryStats(records),
      historyRisk: aiRisk.evaluate({
        statusCode: latest.statusClass === "fall" ? 1 : latest.statusClass === "sitting" ? 2 : 0,
        angle: latest.angle,
        still: latest.still
      }, records)
    });
  },

  clearHistory: function () {
    wx.removeStorageSync(HISTORY_STORAGE_KEY);
    this.setData({
      historyRecords: [],
      historyStats: buildHistoryStats([]),
      historyRisk: aiRisk.evaluate({
        statusCode: 0,
        angle: 90,
        still: 0
      }, [])
    });
  },

  onLoad: function () {
    this.loadHistory();
  },

  onShow: function () {
    this.loadHistory();
  }
});
