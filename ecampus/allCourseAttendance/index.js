const { parse } = require("node-html-parser");
const _ = require("lodash");

const { Axios } = require("axios");
const { constants } = require("crypto");
const { HttpsCookieAgent } = require("http-cookie-agent/http");
const { CookieJar } = require("tough-cookie");
const fs = require("fs").promises;
const { Webhook, MessageBuilder } = require("discord-webhook-node");

const DISCORD_NEW_USER_WEBHOOK_URL = "디스코드 훅 URL";
const DISCORD_INTERNAL_ERROR_WEBHOOK_URL = "디스코드 훅 URL";
const DISCORD_ERROR_WEBHOOK_URL = "디스코드 훅 URL";

class DiscordService {
  constructor(config) {
    this.config = config;
    this.newUserDiscordHook = new Webhook(DISCORD_NEW_USER_WEBHOOK_URL);
    this.internalErrorDiscordHook = new Webhook(
      DISCORD_INTERNAL_ERROR_WEBHOOK_URL
    );
    this.errorDiscordHook = new Webhook(DISCORD_ERROR_WEBHOOK_URL);
  }

  async sendNewUserLog(message) {
    const embed = new MessageBuilder()
      .setTitle("가입알림")
      .setColor(parseInt("0x626FE5", 16))
      .setDescription(message)
      .setTimestamp();
    this.newUserDiscordHook.setUsername("세감 마싯졍");
    await this.newUserDiscordHook.send(embed);
  }

  async sendInternalErrorLog(err, request) {
    const embed = new MessageBuilder()
      .setTitle("🔥🔥🔥🔥🔥500 에러발생🔥🔥🔥🔥🔥")
      .setColor(parseInt("0xDA4237", 16))
      .setDescription(
        `에러발생: ${err.name}\n
        에러메시지: ${err.message}\n
        에러스택: ${err.stack}\n
        요청URL: ${request.url}\n
        요청IP: ${request.ip}\n`
      )
      .setTimestamp();
    this.internalErrorDiscordHook.setUsername("세감 맛없졍");
    await this.internalErrorDiscordHook.send(embed);
  }

  async sendQuitLog(id, name) {
    const embed = new MessageBuilder()
      .setTitle("탈퇴알림")
      .setColor(parseInt("0x626FE5", 16))
      .setDescription(`${id} ${name}님이 탈퇴했습니다.`)
      .setTimestamp();
    this.newUserDiscordHook.setUsername("세감 돌아와");
    await this.newUserDiscordHook.send(embed);
  }

  async sendErrorHTMLLog(user, html) {
    const fileName = Math.random().toString(36).substring(7) + ".html";

    await fs.writeFile("/tmp/" + fileName, html);
    await this.internalErrorDiscordHook.sendFile("/tmp/" + fileName);
    await fs.unlink("/tmp/" + fileName);

    const embed = new MessageBuilder()
      .setTitle("🔥🔥🔥강의 정보 오류 발생🔥🔥🔥")
      .setColor(parseInt("0xDA4237", 16))
      .setDescription(
        `이름: ${user.name}\n
        학번: ${user.studentId}\n
        학과: ${user.departmentName}\n`
      )
      .setTimestamp();
    this.internalErrorDiscordHook.setUsername("세감 맛없졍");
    await this.internalErrorDiscordHook.send(embed);
  }

  async sendErrorLog(err) {
    const embed = new MessageBuilder()
      .setTitle("⚾🥎🏀⚽400 에러발생⚾🥎🏀⚽")
      .setColor(parseInt("0xDA4237", 16))
      .setDescription(
        `에러발생: ${err.name}\n
        에러메시지: ${err.message}\n
        에러스택: ${err.stack}`
      )
      .setTimestamp();
    this.errorDiscordHook.setUsername("세감지켜줘");
    await this.errorDiscordHook.send(embed);
  }
}

class AxiosService extends Axios {
  constructor() {
    const jar = new CookieJar();

    const httpsAgent = new HttpsCookieAgent({
      cookies: { jar },
      secureOptions: constants.SSL_OP_LEGACY_SERVER_CONNECT,
    });

    super({
      withCredentials: true,
      proxy: false,
      httpsAgent,
    });
  }
}

class EcampusService {
  constructor() {
    this.axiosService = new AxiosService();
    this.discordService = new DiscordService();
    this.loginUrl = "https://ecampus.sejong.ac.kr/login/index.php";
    this.dashboardUrl = "https://ecampus.sejong.ac.kr/dashboard.php";
    this.courseUrl = "https://ecampus.sejong.ac.kr/course/view.php";
    this.assignmentUrl = "https://ecampus.sejong.ac.kr/mod/assign/view.php";
  }

  createFormData(username, password) {
    const formData = new FormData();
    formData.append("ssoGubun", "Login");
    formData.append("type", "popup_login");
    formData.append("username", username);
    formData.append("password", password);
    return formData;
  }

  async getAssignmentEndTime(user, id) {
    const res = await this.axiosService.get(this.assignmentUrl + `?id=${id}`);
    try {
      const root = parse(res.data);
      let endsAt = null;

      root.querySelectorAll("tr").forEach((el) => {
        if (!el.querySelector("td.cell.c0")) return;
        if (
          el.querySelector("td.cell.c0").structuredText.trim() ===
            "종료 일시" ||
          el.querySelector("td.cell.c0").structuredText.trim() === "Due date"
        ) {
          endsAt = new Date(el.querySelectorAll("td")[1].structuredText);
        }
      });

      return { id, endsAt };
    } catch (error) {
      throw new Error(
        "과제 정보를 가져오는데 실패했습니다. 다시 시도해주세요."
      );
    }
  }

  async getAllCourseAttendance(user, payload) {
    const loginRequest = await this.axiosService.post(
      this.loginUrl,
      this.createFormData(user.studentId, payload.password)
    );

    if (String(loginRequest.data).indexOf(user.name) === -1) {
      this.discordService.sendErrorLog("로그인 실패");
      throw new Error("로그인 실패");
    }

    const courseList = await this.getCourseList(user, payload, false);

    const courseAttendancePromises = courseList.map((courseId) =>
      this.getCourseAttendance(user, payload, courseId, false)
    );

    const courseAttendances = await Promise.all(courseAttendancePromises);

    return courseAttendances;
  }

  async getCourseAttendance(user, payload, ecampusId, isLoginRequired = true) {
    if (isLoginRequired) {
      const loginRequest = await this.axiosService.post(
        this.loginUrl,
        this.createFormData(user.studentId, payload.password)
      );

      if (String(loginRequest.data).indexOf(user.name) === -1) {
        throw new Error("로그인 실패");
      }
    }

    const res = await this.axiosService.get(
      this.courseUrl + `?id=${ecampusId}`
    );

    try {
      const lectures = [];
      let assignments = [];

      const root = parse(res.data);

      let id;
      let name;

      try {
        const courseInfo = root.querySelector("h2.coursename").structuredText;
        const courseIdRegex = /\((\d{6}-\d{3})\)/;
        id = courseInfo.match(courseIdRegex)[1];
        name = courseInfo.replace(courseIdRegex, "").trim();
      } catch (error) {
        [name, id] = root
          .querySelector("h2.coursename")
          .structuredText.split(" ");
        id = id.slice(1, -1);
      }

      const contents = root.querySelectorAll("li.section.main.clearfix");

      // TODO: 비교과는 제외
      contents.forEach((content) => {
        const week = content.getAttribute("id")?.split("-")[1];
        if (week === "0") return;

        const rawAssignments = content.querySelectorAll(
          "li.activity.assign.modtype_assign"
        );
        const rawLectures = content.querySelectorAll(
          "li.activity.vod.modtype_vod"
        );

        if (!rawAssignments.length && !rawLectures.length) return;
        rawAssignments.forEach((assignment) => {
          if (!assignment.querySelector("span>img")) {
            return;
          }
          const [isSubmitted, name] = assignment
            .querySelector("span>img")
            .getAttribute("alt")
            .split(":");
          const assignmentId = assignment.getAttribute("id").split("-")[1];
          const isDone =
            isSubmitted.trim() === "완료하지 못함" ||
            isSubmitted.trim() === "Not completed"
              ? false
              : true;

          const assignmentData = {
            id: Number(assignmentId),
            name: name.trim(),
            week: parseInt(week),
            isDone,
          };
          assignments.push(assignmentData);
        });

        rawLectures.forEach((lecture) => {
          if (
            !lecture.querySelector("span.text-ubstrap") ||
            !lecture.querySelector("span>img")
          ) {
            return;
          }
          const [isSubmitted, name] = lecture
            .querySelector("span>img")
            .getAttribute("alt")
            .split(":");
          const [startsAt, endsAt] = lecture
            .querySelector("span.text-ubstrap")
            ?.structuredText.split("~");

          const lectureId = lecture.getAttribute("id").split("-")[1];
          const isDone =
            isSubmitted.trim() === "완료하지 못함" ||
            isSubmitted.trim() === "Not completed"
              ? false
              : true;

          const lectureData = {
            id: Number(lectureId),
            name: name.trim(),
            isDone,
            week: parseInt(week),
            startsAt: new Date(startsAt),
            endsAt: new Date(endsAt),
          };
          lectures.push(lectureData);
        });
      });

      const assignmentEndTimes = await Promise.all(
        assignments.map((assignment) =>
          this.getAssignmentEndTime(user, assignment.id)
        )
      );

      assignments = assignments.map((assignment) => {
        const endTime = assignmentEndTimes.find(
          (assignmentEndTime) => assignmentEndTime.id === assignment.id
        );
        return {
          ...assignment,
          endsAt: endTime.endsAt,
        };
      });

      return {
        id: id.trim(),
        name: name.trim(),
        ecampusId,
        lectures: _.uniqBy(lectures, "id"),
        assignments: _.uniqBy(assignments, "id"),
      };
    } catch (error) {
      await this.discordService.sendErrorHTMLLog(user, res.data);
      await this.discordService.sendErrorLog(error);
      throw new Error("강의 에러");
    }
  }

  async getCourseList(user, payload, isLoginRequired = true) {
    if (isLoginRequired) {
      const loginRequest = await this.axiosService.post(
        this.loginUrl,
        this.createFormData(user.studentId, payload.password)
      );

      if (String(loginRequest.data).indexOf(user.name) === -1) {
        throw new Error("로그인 실패");
      }
    }

    const res = await this.axiosService.get(this.dashboardUrl);

    try {
      const root = parse(res.data);
      const contents = root.querySelectorAll("li.course-label-r");

      const courseList = contents.map((content) => {
        const courseId = content
          .querySelector("a")
          .getAttribute("href")
          .split("=")[1];

        return Number(courseId);
      });

      return courseList;
    } catch (error) {
      await this.discordService.sendErrorHTMLLog(user, res.data);
      await this.discordService.sendErrorLog(error);
      throw new Error("강의 에러");
    }
  }
}

exports.handler = async (event) => {
  try {
    const body = JSON.parse(event.body);
    const { studentId, password, name } = body;

    if (!studentId || !password || !name) {
      return {
        statusCode: 400,
        body: JSON.stringify({ error: "Missing required fields" }),
      };
    }

    const ecampusService = new EcampusService();
    const user = { studentId, name };
    const payload = { password };

    const courseAttendances = await ecampusService.getAllCourseAttendance(
      user,
      payload
    );

    return {
      statusCode: 200,
      body: JSON.stringify(courseAttendances),
    };
  } catch (error) {
    let statusCode = 500;
    let errorMessage = "Internal server error";

    if (error.message === "로그인 실패") {
      statusCode = 401;
      errorMessage = error.message;
    } else if (error.message === "강의 에러") {
      statusCode = 400;
      errorMessage = error.message;
    }

    return {
      statusCode: statusCode,
      body: JSON.stringify({ error: errorMessage }),
    };
  }
};
