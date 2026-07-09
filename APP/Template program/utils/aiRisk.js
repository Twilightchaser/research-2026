function toNumber(value, fallback) {
  var number = Number(value);

  if (isNaN(number)) {
    return fallback;
  }

  return number;
}

function countRecent(records, statusClass) {
  return records.filter(function (record) {
    return record.statusClass === statusClass;
  }).length;
}

function evaluate(current, records) {
  records = records || [];

  var statusCode = toNumber(current.statusCode, 0);
  var angle = toNumber(current.angle, 90);
  var still = toNumber(current.still, 0);
  var fallCount = countRecent(records, "fall");
  var sittingCount = countRecent(records, "sitting");
  var score = 10;
  var reason = "当前状态平稳，历史异常较少。";
  var advice = "继续保持设备在线，定时查看同步时间即可。";
  var level = "低风险";
  var riskClass = "normal";

  if (statusCode === 1) {
    score = 92;
    reason = "当前检测到疑似跌倒，姿态角低于安全阈值。";
    advice = "建议立即电话联系老人，必要时到现场确认安全。";
    level = "高风险";
    riskClass = "fall";
  } else if (statusCode === 2) {
    score = 64;
    reason = "当前处于久坐状态，静止时间已经超过提醒阈值。";
    advice = "建议提醒老人缓慢起身活动，避免突然站立。";
    level = "中风险";
    riskClass = "sitting";
  } else {
    score = Math.max(8, Math.min(35, 35 - Math.round(angle / 4)));
  }

  if (fallCount >= 2 && statusCode !== 1) {
    score = Math.max(score, 76);
    reason = "最近记录中出现多次疑似跌倒，需要复核设备佩戴和老人状态。";
    advice = "建议联系老人确认，并检查传感器固定位置。";
    level = "较高风险";
    riskClass = "fall";
  } else if (sittingCount >= 3 && statusCode !== 1) {
    score = Math.max(score, 68);
    reason = "最近记录中久坐次数较多，活动不足风险升高。";
    advice = "建议安排定时活动提醒，并观察是否频繁久坐。";
    level = "中风险";
    riskClass = "sitting";
  }

  return {
    score: score,
    level: level,
    riskClass: riskClass,
    reason: reason,
    advice: advice,
    basis: "综合当前状态、姿态角和最近 " + records.length + " 条历史记录"
  };
}

module.exports = {
  evaluate: evaluate
};
