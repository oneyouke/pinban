# Desktop Imposer Pro V3.0

V3.0 独立增量模块目录。当前仅建立架构边界，尚未接管 V2.4.x 的生产入口。

## 约束

- 不删除、不移动 V2.4.x 现有模块。
- 不复制旧版拼版算法；先审计，再通过 adapter 复用。
- 任何新算法必须有单元测试和 PDF golden test。
- Qt UI 与拼版业务逻辑分离。
- 以 point/mm 明确单位，不使用隐式坐标换算。

详见：
- [源码审查](../docs/V3.0_SOURCE_AUDIT.md)
- [架构设计](../docs/V3.0_ARCHITECTURE.md)
- [开发路线图](../docs/V3.0_ROADMAP.md)
