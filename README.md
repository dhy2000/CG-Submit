# CourseGrading 自动提交工具

基于 CourseGrading （简称 CG）课程平台的文件自动提交脚本，可用于自动提交文件至指定题目或提交相同文件至多道题目，并取回评测结果。

适用范围：北航信息大类《数据结构与程序设计》/计算机学院《编译技术》课程平台，其他基于 CG 的课程平台（该脚本仅保证 2021 年秋季学期可用，不保证未来 CG 平台如有更新后继续可用）。

## 使用说明

### 1. 获取必需的参数

> 注：在阅读本部分前推荐预先掌握如下内容：
> - HTTP 请求的基本种类和格式（请求头， GET 请求的参数）
> - 浏览器开发者模式，或任一种抓包软件的使用

首先登录 CG 课程平台帐号，（如帐号同时属于多门课程则需要选择课程），进入在线作业，打开需要提交的作业的一道具体题目（编程题/文件提交题），而后启动浏览器开发者模式或抓包软件，刷新网页并记录所有 HTTP 请求。

除登录课程平台的用户名和密码外，使用本自动提交工具需要获取并记录的参数字段包括：

- `courseID`,  `assignID`：在查看题目页面的地址栏或开发者模式下记录的第一个 GET 请求地址中即可找到此字段，此二字段为题目查看页面 GET 请求的参数。（例如：`GET /assignment/programOJPList.jsp?proNum=*&courseID=**&assignID=***`）
- `problemID`：开发者模式或抓包软件记录下的请求中，找出访问 `showOJPProcessJSON.jsp` 的 GET 请求，该字段为该 GET 请求的参数。（例如：`GET /assignment/showOJPProcessJSON.jsp?assignID=***&problemID=***&userID=********&buaa=*.********`，`assignID` 字段也在该请求中）

> 以上请求地址示例仅表示格式，各参数的实际值以 `*` 号代替。

记录下登录用户名，密码以及上述的四个参数后，即可开始编写配置文件。

### 2. 编写配置文件

注：在以下表述中用**当前目录**指代 **`cg_submit.py`脚本文件所在的目录**。

在当前目录中创建一个名为 `cg_config.json` 的配置文件（在仓库中已经给出配置文件模板 `cg_config_sample.json`，可直接修改文件名为 `cg_config.json`），并按照下方的配置说明填入相应的参数。

配置文件采用 JSON 格式，参考模板及各字段含义如下：
```jsonc
{
    "root-url": "http://judge.buaa.edu.cn", // 课程网站地址
    "request": {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:92.0) Gecko/20100101 Firefox/92.0" // HTTP 请求头中的 User-Agent 字段，与客户端使用的浏览器有关, 可不修改
    },
    "login": {
        "username": "19373000", // 用户名, 通常为学号
        "password": "????????",   // 登录密码(明文形式! 填写时注意保护隐私)
        "courseID": "10"    // 课程 ID, "courseID" 参数
    },
    "submit": [ // 此处为一个 JSON 数组，一个元素代表一道题目
        {
            "assignID": "1004", // 题目的 "assignID" 参数
            "problemID": "6671" // 题目的 "problemID" 参数
        },
        {
            "assignID": "1004",
            "problemID": "6672"
        },
        {
            "assignID": "1004",
            "problemID": "6673"
        }
    ],
    "save-result": true // 是否取回并保存评测结果(HTML 格式)
}
```

> 特别提醒：在实际编写 JSON 配置文件时请**不要包含注释**！


### 3. 在命令行中运行

完成编写配置文件并命名为 `cg_config.json` 后，执行如下命令（假设要提交的文件名为 `file.zip` 并置于当前目录）：

```sh
python -u cg_submit.py file.zip
```

若编写了多套配置文件或配置文件名称不是 `cg_config.json`，也可使用命令参数指定配置文件，参数格式为 `-c [config.json]`，其中 `[config.json]` 为实际使用的配置文件名。

示例：使用配置 `config1.json` 提交 `file.zip`

```sh
python -u cg_submit.py -c config1.json file.zip
```

或 

```sh
python -u cg_submit.py file.zip -c config1.json
```

（注意：若不用 `-c` 参数指定选择的配置文件，则默认使用当前目录下的 `cg_config.json`）

说明：

1. 若直接执行 `python` 命令打开的是 Python 2 则请使用 `python3` ，若找不到命令，则请将 `python` 替换为 Python 解释程序的绝对路径或将其加入 `PATH` 环境变量中。
2. 若要提交的文件名不是 `file.zip` 或不位于当前目录下，请将上述命令示例中的 `file.zip` 替换成实际提交的文件路径(相对路径或绝对路径均可)。
3. 若设定了 `save-result` 参数，则评测结果以 HTML 文件形式保存在当前目录下，每道题目一个 HTML 文件。
