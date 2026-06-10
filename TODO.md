# HK Data Pipeline — 进度追踪

## ✅ 已完成
- [x] 项目结构搭建
- [x] `weather_report.py` — Open-Meteo 天气数据 → GCS
- [x] `air_quality.py` — Open-Meteo 空气质量数据 → GCS
- [x] `gcs_to_bq.py` — GCS → BigQuery
- [x] `utils.py` — 共享工具函数（GCS 上传、GCP 凭证）
- [x] dbt 配置（staging 去重 + mart 聚合），本地跑通
- [x] `mart_daily_combined.sql` — 天气 + 空气质量 joined mart
- [x] Docker 镜像 build（`ingestion:latest`, `dbt:latest`）
- [x] 镜像推到 Artifact Registry
- [x] GCP VM 创建（`kestra-vm`, `asia-east2-a`, `e2-small`）
- [x] VM 上安装 Docker + Kestra
- [x] Orchestration 重构（subflow 架构：ingest / load / transform）
- [x] `push_flows.sh` — 一键推送所有 flows 到 Kestra
- [x] Flows 推送到 VM Kestra

## 🔄 进行中
- [ ] VM Kestra 配置 KV Store：`GCP_SERVICE_ACCOUNT_KEY`
- [ ] 启用 daily_pipeline schedule trigger
- [ ] 端到端测试跑通（VM）

## 📋 待完成
- [ ] 历史数据回填（2025-06-10 至今，用 backfill_ingest + daily_etl）
- [ ] dbt test 全部通过
- [ ] Looker Studio 看板搭建（基于 mart_daily_combined）
- [ ] README 完善（架构图、截图、运行说明）
- [ ] 代码 push 到 GitHub
