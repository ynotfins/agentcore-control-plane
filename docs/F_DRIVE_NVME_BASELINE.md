# F Drive NVMe Baseline

Generated: 2026-06-21

## Current Role

`F:` is now the `Agent_Vector_4TB` Samsung 990 Pro with Heatsink and hosts the active AgentCore runtime:

- PostgreSQL engine: `F:\AgentCore\postgres_runtime_engine\pgsql`
- PostgreSQL data cluster: `F:\AgentCore\database_cluster`
- Agent workspaces: `F:\AgentCore\agents_workspace`
- Ingestion staging: `F:\AgentCore\ingestion_staging`

The 6 TB external drive is now the cold archive/data lake:

`E:\AgentCoreArchive`

## Current Windows Disk Identity

Previous `F:` baseline was the old 128 GB external NVMe bridge:

- Model: `JMicron Tech SCSI Disk Device`
- Interface: `SCSI`
- Media: external hard disk media
- Size: about `128 GB`
- Volume label: `NVME M.2 118GB`
- Free space before move: about `117 GB`

This indicates the drive is currently behind an external JMicron USB/SCSI bridge. That bridge likely limits throughput compared to installing the NVMe drive in a motherboard M.2 slot.

Current `F:` identity:

- Model: `Samsung SSD 990 PRO with Heatsink 4TB`
- Volume label: `Agent_Vector_4TB`
- Filesystem: NTFS
- Allocation unit: 64 KB
- Size: about 4 TB

## Motherboard

- Manufacturer: ASUSTeK COMPUTER INC.
- Product: `Z790 GAMING WIFI7`
- Version: Rev 1.xx

Firmware-reported M.2 slots:

| Slot | Firmware Usage | Recommendation |
| --- | --- | --- |
| `M.2_1` | In use | Do not use unless intentionally replacing/moving an existing drive |
| `M.2_2` | Available | Best candidate for the F: drive move |
| `M.2_3` | In use | Do not use unless intentionally replacing/moving an existing drive |
| `M.2(WIFI)` | In use | Wi-Fi slot, not for this database drive |

ASUS documentation for `Z790 GAMING WIFI7` states:

- `M.2_1`: CPU-connected, PCIe 4.0 x4, 2242/2260/2280/22110
- `M.2_2`: Z790 chipset, PCIe 4.0 x4, 2242/2260/2280
- `M.2_3`: Z790 chipset, PCIe 4.0 x4 plus SATA, 2242/2260/2280/22110

Use `M.2_2` first if the physical board layout matches the firmware report.

## Baseline Performance Old External 128 GB F

Windows `winsat disk -drive F` results while the drive was external:

```text
Disk Random 16.0 Read                       280.61 MB/s
Disk Sequential 64.0 Read                   389.43 MB/s
Disk Sequential 64.0 Write                  385.50 MB/s
Average Read Time with Sequential Writes    0.208 ms
Latency: 95th Percentile                    0.403 ms
Latency: Maximum                            3.680 ms
Average Read Time with Random Writes        0.230 ms
```

## Baseline Performance Samsung 990 Pro 4 TB Internal F

Windows `winsat disk -drive F` results after installation:

```text
Disk Random 16.0 Read                       3301.29 MB/s
Disk Sequential 64.0 Read                   6159.93 MB/s
Disk Sequential 64.0 Write                  7017.93 MB/s
Average Read Time with Sequential Writes    0.037 ms
Latency: 95th Percentile                    0.088 ms
Latency: Maximum                            0.192 ms
Average Read Time with Random Writes        0.031 ms
```

Improvement over old external bridge:

- Sequential read: about 15.8x faster
- Sequential write: about 18.2x faster
- 95th percentile latency: about 4.6x lower

## Post-Move Comparison

After future drive maintenance, run:

```powershell
winsat disk -drive F
```

Then run:

```powershell
D:\MCP-Control-Plane\ops\Start-AgentCorePostgres.ps1 -StartIfStopped
```

Expected health checks:

- engine root: passed
- `pg_ctl`: passed
- server status: passed
- pgvector extension: passed
- vector table query: passed

## Important

Keep the drive letter as `F:` if possible. The control-plane contract and PostgreSQL helper scripts currently expect:

`F:\AgentCore\postgres_runtime_engine\pgsql`
