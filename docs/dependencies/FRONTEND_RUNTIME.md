# Phase 2B 前端运行依赖

安装日期：2026-09-05。Node v22.17.1、npm 10.9.2。项目使用 `frontend/package.json` 精确版本与 lockfile integrity，不使用 `latest` 或范围。核心：React/React DOM 19.2.8、Vite 8.2.2、TypeScript 7.0.2、Vitest 5.0.0；测试包清单以 package.json 为准。

官方依据：[React 当前 19.2](https://react.dev/versions)、[Vite 起步与 Node 要求](https://vite.dev/guide/)、[Testing Library React 安装](https://testing-library.com/docs/react-testing-library/intro/)、[Vitest 清理配置](https://testing-library.com/docs/react-testing-library/setup/)、[npm registry 与 lockfile 语义](https://docs.npmjs.com/using-npm/registry.html/)。npm view 在施工日给出实际精确 patch 版本。

初选 jsdom 30.0.1 报 engine 需要 Node 22.22.2 以上，改为 jsdom 29.1.1，其声明兼容 Node 22.13 以上；安装后无 engine 警告。默认系统 npm registry 是 npmmirror，生成的 resolved 地址因此指向该镜像，文件仍包含 integrity。尝试只用官方 registry 重写时 npm 复用了既有/隐藏锁，检查失败后均恢复原锁，没有手工改 integrity；官方 `npm audit --omit=dev --audit-level=high --registry=https://registry.npmjs.org` 返回 0 vulnerabilities。此结果不是完整供应链或未来漏洞保证。

安装始终使用 `--ignore-scripts`。生产运行依赖只有 React/React DOM；Vite、TypeScript、jsdom 和测试工具均为 devDependencies。页面无 CDN、远程字体、分析脚本或默认上传；本地 API 不提供 CORS。
