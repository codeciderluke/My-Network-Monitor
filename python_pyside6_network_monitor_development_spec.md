# 실시간 네트워크 트래픽 모니터 개발 명세

## 1. 프로젝트 개요

Python과 PySide6를 사용하여 Windows 환경에서 동작하는 실시간 네트워크 트래픽 모니터링 GUI 애플리케이션을 개발한다.

애플리케이션은 다음 두 영역을 중심으로 구성한다.

- 왼쪽 패널: 사용자가 이해하기 쉬운 주요 네트워크 상태와 요약 정보
- 오른쪽 패널: 실시간으로 수집되는 상세 네트워크 트래픽 로그

초기 버전은 네트워크 패킷의 L3/L4 메타데이터를 중심으로 구현하며, HTTPS 통신 내용 복호화나 패킷 차단 기능은 범위에서 제외한다.

---

## 2. 개발 목표

### 2.1 핵심 목표

1. 유선 및 무선 네트워크 인터페이스 목록을 조회할 수 있어야 한다.
2. 사용자가 선택한 인터페이스의 트래픽을 실시간으로 캡처해야 한다.
3. 송신 및 수신 트래픽을 구분해야 한다.
4. TCP, UDP, DNS, ICMP, IPv4, IPv6 정보를 분석해야 한다.
5. 현재 업로드 및 다운로드 속도를 표시해야 한다.
6. 실시간 트래픽 추이 그래프를 표시해야 한다.
7. 상세 트래픽 로그를 테이블 형태로 표시해야 한다.
8. 대량의 패킷이 발생해도 GUI가 멈추지 않아야 한다.
9. 프로토콜, IP 주소, 포트, 방향을 기준으로 로그를 필터링할 수 있어야 한다.
10. 전체 로그를 파일 또는 SQLite에 저장할 수 있어야 한다.

### 2.2 비기능 목표

- UI 스레드에서 패킷 캡처나 무거운 파싱 작업을 실행하지 않는다.
- 화면에는 최근 로그만 유지하여 메모리 사용량 증가를 제한한다.
- 패킷 캡처 큐에는 최대 크기를 설정한다.
- UI 갱신은 패킷 단위가 아니라 배치 단위로 수행한다.
- 캡처 종료 시 스레드와 리소스를 정상적으로 정리한다.
- 관리자 권한이나 Npcap 미설치 상태를 사용자에게 명확히 안내한다.

---

## 3. 대상 환경

### 3.1 우선 지원 환경

- 운영체제: Windows 10, Windows 11
- Python: 3.12 이상
- GUI: PySide6
- 패킷 캡처 드라이버: Npcap
- 패키지 관리: uv 또는 Poetry
- 빌드 및 배포: PyInstaller

### 3.2 향후 지원 가능 환경

- Linux
- macOS

초기 구현에서는 Windows 지원을 우선하며, 운영체제 의존 코드는 별도 모듈로 분리한다.

---

## 4. 권장 기술 스택

| 구분 | 기술 |
|---|---|
| 언어 | Python 3.12+ |
| GUI | PySide6 |
| 패킷 캡처 | Scapy 또는 pcap 계열 라이브러리 |
| 그래프 | pyqtgraph |
| 프로세스 정보 | psutil |
| 비동기 큐 | queue.Queue |
| 데이터 저장 | SQLite |
| ORM 또는 쿼리 | sqlite3 또는 SQLAlchemy |
| 로깅 | Python logging |
| 테스트 | pytest |
| 코드 품질 | Ruff, mypy |
| 패키징 | PyInstaller |

### 4.1 패킷 캡처 라이브러리 선택

초기 MVP에서는 Scapy를 사용할 수 있다.

Scapy를 사용할 때는 다음 사항을 고려한다.

- Windows에서 Npcap 설치 필요
- 관리자 권한이 필요할 수 있음
- 대량 트래픽에서는 Python 객체 생성 비용이 커질 수 있음
- 캡처 콜백에서 복잡한 작업을 하지 말고 즉시 큐로 전달해야 함

성능 문제가 발생하면 다음 대안을 검토한다.

- python-libpcap
- pcapy-ng
- 별도의 Rust 캡처 엔진
- 별도의 네이티브 캡처 프로세스

---

## 5. 프로젝트 구조

```text
network-traffic-monitor/
├─ pyproject.toml
├─ README.md
├─ requirements.txt
├─ assets/
│  ├─ icons/
│  └─ styles/
├─ src/
│  └─ network_monitor/
│     ├─ __init__.py
│     ├─ main.py
│     ├─ config.py
│     ├─ logging_config.py
│     │
│     ├─ domain/
│     │  ├─ __init__.py
│     │  ├─ packet_record.py
│     │  ├─ traffic_snapshot.py
│     │  ├─ network_interface.py
│     │  └─ alert.py
│     │
│     ├─ capture/
│     │  ├─ __init__.py
│     │  ├─ capture_service.py
│     │  ├─ scapy_capture_service.py
│     │  ├─ interface_service.py
│     │  └─ capture_worker.py
│     │
│     ├─ analysis/
│     │  ├─ __init__.py
│     │  ├─ packet_parser.py
│     │  ├─ traffic_aggregator.py
│     │  ├─ connection_tracker.py
│     │  ├─ process_resolver.py
│     │  └─ alert_detector.py
│     │
│     ├─ storage/
│     │  ├─ __init__.py
│     │  ├─ database.py
│     │  ├─ traffic_repository.py
│     │  └─ export_service.py
│     │
│     ├─ ui/
│     │  ├─ __init__.py
│     │  ├─ main_window.py
│     │  ├─ models/
│     │  │  ├─ traffic_table_model.py
│     │  │  └─ process_table_model.py
│     │  ├─ widgets/
│     │  │  ├─ metric_card.py
│     │  │  ├─ traffic_chart.py
│     │  │  ├─ traffic_filter_bar.py
│     │  │  ├─ traffic_log_table.py
│     │  │  └─ packet_detail_dialog.py
│     │  └─ controllers/
│     │     └─ main_controller.py
│     │
│     └─ utils/
│        ├─ formatters.py
│        ├─ ip_utils.py
│        └─ ring_buffer.py
│
└─ tests/
   ├─ test_packet_parser.py
   ├─ test_traffic_aggregator.py
   ├─ test_traffic_table_model.py
   └─ fixtures/
```

---

## 6. 전체 아키텍처

```text
Npcap / Scapy
      │
      ▼
Capture Worker Thread
      │
      ▼
Bounded Raw Packet Queue
      │
      ▼
Parser Worker Thread
      │
      ├── Parsed Packet Queue
      ├── Traffic Aggregator
      ├── Connection Tracker
      └── Process Resolver
              │
              ▼
        UI Batch Buffer
              │
              ▼
      QTimer-based UI Refresh
              │
      ┌───────┴────────┐
      ▼                ▼
Summary Panel      Traffic Log Table
```

### 6.1 핵심 설계 원칙

- 패킷 캡처와 GUI를 완전히 분리한다.
- 캡처 콜백에서는 패킷을 큐에 넣는 작업만 수행한다.
- 패킷 파싱은 별도의 워커 스레드에서 수행한다.
- GUI는 QTimer를 사용해 일정 주기로 결과를 가져온다.
- 패킷마다 Qt Signal을 발행하지 않는다.
- 상세 로그는 고정 크기 링 버퍼로 관리한다.
- 저장 기능은 별도의 저장 워커를 사용한다.

---

## 7. GUI 요구사항

## 7.1 메인 화면

```text
┌────────────────────────────────────────────────────────────────────┐
│ Network Traffic Monitor     Interface: Wi-Fi ▼   ● Capture Running │
├───────────────────────────┬────────────────────────────────────────┤
│ 주요 트래픽 현황          │ 상세 트래픽 로그                       │
│                           │                                        │
│ Download      12.4 MB/s   │ Time     Dir Proto Source → Destination│
│ Upload         2.1 MB/s   │ 12:01:20 OUT TCP  192.168.0.2 → ...    │
│ Connections          42   │ 12:01:20 OUT DNS  192.168.0.2 → ...    │
│                           │ 12:01:21 IN  TCP  142.250... → ...      │
│ [실시간 속도 그래프]      │                                        │
│                           │ [Protocol] [IP] [Port] [Search]         │
│ Top Processes             │                                        │
│ chrome.exe       5.2 MB/s │                                        │
│ python.exe       2.4 MB/s │                                        │
│ Code.exe         1.1 MB/s │                                        │
│                           │                                        │
│ Alerts                    │                                        │
│ High upload traffic       │                                        │
└───────────────────────────┴────────────────────────────────────────┘
```

### 7.2 상단 툴바

포함 항목:

- 네트워크 인터페이스 선택 콤보박스
- 캡처 시작 버튼
- 캡처 중지 버튼
- 일시정지 버튼
- 로그 초기화 버튼
- PCAP 저장 여부
- SQLite 저장 여부
- 설정 버튼
- 현재 캡처 상태 표시

### 7.3 왼쪽 요약 패널

표시 항목:

- 현재 다운로드 속도
- 현재 업로드 속도
- 누적 다운로드 용량
- 누적 업로드 용량
- 초당 패킷 수
- 활성 연결 수
- TCP 패킷 수
- UDP 패킷 수
- DNS 패킷 수
- ICMP 패킷 수
- 최근 60초 업로드 및 다운로드 그래프
- 트래픽 상위 프로세스
- 트래픽 상위 목적지
- 최근 경고

### 7.4 오른쪽 상세 로그 패널

로그 컬럼:

| 컬럼 | 설명 |
|---|---|
| Time | 패킷 캡처 시각 |
| Direction | IN 또는 OUT |
| Interface | 캡처 인터페이스 |
| Protocol | TCP, UDP, DNS, ICMP 등 |
| Process | 프로세스 이름 |
| PID | 프로세스 ID |
| Source | 출발지 IP |
| Source Port | 출발지 포트 |
| Destination | 목적지 IP |
| Destination Port | 목적지 포트 |
| Size | 패킷 크기 |
| Summary | 패킷 요약 |

### 7.5 상세 로그 기능

- 프로토콜 필터
- 방향 필터
- IP 주소 검색
- 포트 검색
- 프로세스 검색
- 일시정지
- 자동 스크롤
- 선택 행 복사
- CSV 내보내기
- JSON Lines 내보내기
- 패킷 상세 다이얼로그
- 선택한 행의 원본 바이트를 16진수로 표시

---

## 8. 도메인 모델

### 8.1 PacketRecord

```python
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class TrafficDirection(StrEnum):
    INBOUND = "IN"
    OUTBOUND = "OUT"
    UNKNOWN = "UNKNOWN"


@dataclass(slots=True)
class PacketRecord:
    timestamp: datetime
    interface_name: str
    direction: TrafficDirection
    protocol: str
    source_ip: str
    destination_ip: str
    source_port: int | None
    destination_port: int | None
    length: int
    process_name: str | None = None
    process_id: int | None = None
    domain_name: str | None = None
    summary: str = ""
    raw_bytes: bytes | None = None
```

### 8.2 TrafficSnapshot

```python
from dataclasses import dataclass, field


@dataclass(slots=True)
class TrafficSnapshot:
    download_bytes_per_second: float = 0
    upload_bytes_per_second: float = 0
    total_download_bytes: int = 0
    total_upload_bytes: int = 0
    packets_per_second: int = 0
    active_connections: int = 0
    protocol_counts: dict[str, int] = field(default_factory=dict)
    top_processes: list[tuple[str, int]] = field(default_factory=list)
    top_destinations: list[tuple[str, int]] = field(default_factory=list)
```

---

## 9. 패킷 캡처 구현

## 9.1 CaptureService 인터페이스

```python
from abc import ABC, abstractmethod
from collections.abc import Callable


class CaptureService(ABC):
    @abstractmethod
    def list_interfaces(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def start(
        self,
        interface_name: str,
        packet_callback: Callable[[object], None],
        bpf_filter: str | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def is_running(self) -> bool:
        raise NotImplementedError
```

## 9.2 Scapy 캡처 서비스

구현 시 `AsyncSniffer`를 우선 검토한다.

```python
from scapy.all import AsyncSniffer


class ScapyCaptureService(CaptureService):
    def __init__(self) -> None:
        self._sniffer: AsyncSniffer | None = None

    def start(
        self,
        interface_name: str,
        packet_callback,
        bpf_filter: str | None = None,
    ) -> None:
        if self._sniffer is not None:
            raise RuntimeError("Capture is already running.")

        self._sniffer = AsyncSniffer(
            iface=interface_name,
            prn=packet_callback,
            store=False,
            filter=bpf_filter,
        )
        self._sniffer.start()

    def stop(self) -> None:
        if self._sniffer is None:
            return

        self._sniffer.stop()
        self._sniffer = None

    @property
    def is_running(self) -> bool:
        return self._sniffer is not None
```

### 9.3 캡처 콜백 제한

캡처 콜백에서는 다음 작업만 수행한다.

1. 현재 시각 기록
2. 패킷 객체를 bounded queue에 삽입
3. 큐가 가득 찬 경우 드롭 카운터 증가
4. 즉시 반환

캡처 콜백에서 금지할 작업:

- DNS 역조회
- 프로세스 조회
- SQLite 저장
- GUI 업데이트
- 복잡한 문자열 변환
- 파일 기록
- 상세 패킷 파싱

---

## 10. 큐 및 백프레셔

Python의 `queue.Queue`에 최대 크기를 지정한다.

```python
from queue import Full, Queue


raw_packet_queue: Queue = Queue(maxsize=50_000)


def enqueue_packet(packet: object) -> None:
    try:
        raw_packet_queue.put_nowait(packet)
    except Full:
        dropped_packet_counter.increment()
```

### 10.1 큐 정책

- raw packet queue: 최대 50,000건
- parsed packet queue: 최대 20,000건
- UI pending queue: 최대 10,000건
- 저장 queue: 최대 50,000건

큐가 가득 찬 경우:

- 캡처를 중단하지 않는다.
- 오래된 UI 로그 또는 신규 상세 로그 일부를 버릴 수 있다.
- 집계 정보는 가능하면 유지한다.
- 드롭된 패킷 수를 UI에 표시한다.

---

## 11. 패킷 파싱

## 11.1 지원 프로토콜

MVP 지원:

- Ethernet
- IPv4
- IPv6
- TCP
- UDP
- DNS
- ICMP
- ARP

후속 지원:

- DHCP
- TLS ClientHello 메타데이터
- HTTP 평문 요청
- QUIC 메타데이터

### 11.2 패킷 파서 책임

- IP 주소 추출
- 포트 추출
- 프로토콜 분류
- 패킷 길이 계산
- TCP 플래그 요약
- DNS 질의명 추출
- ICMP 타입 요약
- 트래픽 방향 판별
- PacketRecord 생성

### 11.3 방향 판별

로컬 인터페이스의 IP 주소 목록을 유지한다.

```text
source_ip가 로컬 IP이고 destination_ip가 외부 IP이면 OUT
destination_ip가 로컬 IP이고 source_ip가 외부 IP이면 IN
둘 다 로컬이면 LOCAL
판별할 수 없으면 UNKNOWN
```

루프백 트래픽은 별도 옵션으로 표시한다.

---

## 12. 트래픽 집계

### 12.1 집계 주기

- 내부 집계: 패킷 수신 시
- 화면 스냅샷 생성: 500ms 또는 1초
- 그래프 데이터 유지: 최근 60초
- 프로세스 순위 계산: 1초
- 활성 연결 정리: 5초

### 12.2 집계 항목

- 초당 다운로드 바이트
- 초당 업로드 바이트
- 누적 다운로드 바이트
- 누적 업로드 바이트
- 초당 패킷 수
- 프로토콜별 패킷 수
- 프로세스별 바이트 수
- 목적지별 바이트 수
- 인터페이스별 바이트 수
- 연결별 바이트 수
- 드롭된 패킷 수

### 12.3 Sliding Window

최근 60초 그래프를 위해 `collections.deque(maxlen=60)`를 사용한다.

```python
from collections import deque


download_history = deque(maxlen=60)
upload_history = deque(maxlen=60)
```

---

## 13. 프로세스 매핑

패킷 자체에는 PID가 포함되지 않으므로 별도의 연결 테이블 조회가 필요하다.

### 13.1 MVP 구현

`psutil.net_connections(kind="inet")`를 일정 주기로 조회한다.

매핑 키:

```text
protocol
local_ip
local_port
remote_ip
remote_port
```

프로세스 이름 조회:

```python
import psutil


def resolve_process_name(pid: int | None) -> str | None:
    if pid is None:
        return None

    try:
        return psutil.Process(pid).name()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None
```

### 13.2 주의사항

- 매우 짧은 연결은 놓칠 수 있다.
- UDP는 remote endpoint 정보가 없을 수 있다.
- 관리자 권한이 없으면 일부 프로세스 정보 접근이 제한될 수 있다.
- 매 패킷마다 `psutil.net_connections()`를 호출하면 안 된다.
- 연결 테이블은 500ms에서 2초 간격으로 캐싱한다.

### 13.3 향후 고도화

- Windows IP Helper API
- ETW 네트워크 이벤트
- 별도 Rust 또는 C++ 네이티브 모듈

---

## 14. PySide6 스레딩 모델

### 14.1 권장 구성

- UI Thread
- Capture Thread
- Parser Thread
- Storage Thread
- Process Resolver Thread

### 14.2 UI 업데이트 방식

`QTimer`로 주기적으로 큐에서 데이터를 가져온다.

```python
from PySide6.QtCore import QTimer


self.ui_timer = QTimer(self)
self.ui_timer.setInterval(250)
self.ui_timer.timeout.connect(self.flush_pending_data)
self.ui_timer.start()
```

### 14.3 한 번에 반영할 최대 로그 수

```python
MAX_LOGS_PER_UI_TICK = 300
MAX_VISIBLE_LOG_ROWS = 10_000
```

패킷마다 Qt Signal을 발생시키는 방식은 피한다.

---

## 15. 상세 로그 테이블

`QTableWidget`을 사용하지 않는다.

반드시 다음 구조를 사용한다.

- `QTableView`
- `QAbstractTableModel`
- 고정 크기 링 버퍼
- 필요한 경우 `QSortFilterProxyModel`

### 15.1 모델 기본 구조

```python
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


class TrafficTableModel(QAbstractTableModel):
    HEADERS = [
        "Time",
        "Direction",
        "Protocol",
        "Process",
        "Source",
        "Destination",
        "Size",
        "Summary",
    ]

    def __init__(self, max_rows: int = 10_000) -> None:
        super().__init__()
        self._rows = []
        self._max_rows = max_rows

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None

        record = self._rows[index.row()]
        return self._get_cell_value(record, index.column())
```

### 15.2 배치 추가

여러 건을 한 번에 추가한다.

- `beginInsertRows`
- 리스트 extend
- `endInsertRows`

최대 행 수를 초과하면 오래된 행을 배치 삭제한다.

---

## 16. 필터 기능

### 16.1 기본 필터

- Protocol: All, TCP, UDP, DNS, ICMP, ARP
- Direction: All, IN, OUT
- Process name
- Source IP
- Destination IP
- Source port
- Destination port
- Minimum packet size
- 텍스트 검색

### 16.2 BPF 필터

캡처 전에 적용 가능한 필터 예시:

```text
ip or ip6
tcp
udp
port 53
host 8.8.8.8
tcp port 443
```

화면 필터와 캡처 필터는 구분한다.

- Capture Filter: 실제 캡처되는 패킷을 제한
- Display Filter: 캡처된 로그 중 화면에 표시할 항목을 제한

---

## 17. 그래프

`pyqtgraph`를 사용한다.

표시 데이터:

- 최근 60초 다운로드 속도
- 최근 60초 업로드 속도
- 선택적으로 초당 패킷 수

### 17.1 그래프 갱신 주기

- 500ms 또는 1초
- 그래프 포인트 최대 60개 또는 120개
- 패킷마다 redraw하지 않는다.

### 17.2 단위 자동 변환

- B/s
- KB/s
- MB/s
- GB/s

---

## 18. 저장 기능

### 18.1 SQLite 저장

테이블 예시:

```sql
CREATE TABLE IF NOT EXISTS traffic_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    interface_name TEXT NOT NULL,
    direction TEXT NOT NULL,
    protocol TEXT NOT NULL,
    source_ip TEXT,
    source_port INTEGER,
    destination_ip TEXT,
    destination_port INTEGER,
    packet_length INTEGER NOT NULL,
    process_name TEXT,
    process_id INTEGER,
    domain_name TEXT,
    summary TEXT
);
```

인덱스:

```sql
CREATE INDEX IF NOT EXISTS idx_traffic_timestamp
ON traffic_log(timestamp);

CREATE INDEX IF NOT EXISTS idx_traffic_protocol
ON traffic_log(protocol);

CREATE INDEX IF NOT EXISTS idx_traffic_destination
ON traffic_log(destination_ip, destination_port);
```

### 18.2 배치 저장

패킷마다 commit하지 않는다.

- 100건 이상 모이면 저장
- 또는 1초마다 저장
- `executemany()` 사용
- 저장 실패 시 UI에 오류 표시
- 저장 워커가 GUI를 차단하지 않도록 구성

### 18.3 내보내기 형식

- CSV
- JSON Lines
- SQLite
- PCAP

PCAP 저장은 Scapy의 packet 객체 또는 raw bytes를 별도 큐에 전달하여 처리한다.

---

## 19. 패킷 상세 다이얼로그

선택한 로그를 더블클릭하면 상세 창을 연다.

표시 항목:

- 기본 정보
- Ethernet 헤더
- IP 헤더
- TCP 또는 UDP 헤더
- TCP 플래그
- DNS 정보
- 패킷 길이
- 원본 바이트 Hex View
- ASCII View

민감정보 노출 가능성을 고려하여 raw payload 저장 여부를 설정에서 선택할 수 있어야 한다.

기본 설정은 payload 미저장으로 한다.

---

## 20. 예외 및 오류 처리

사용자에게 안내해야 할 상황:

- Npcap 미설치
- 관리자 권한 부족
- 인터페이스 조회 실패
- 인터페이스가 사라짐
- 캡처 시작 실패
- 캡처 중 예외
- SQLite 쓰기 실패
- 디스크 공간 부족
- 패킷 큐 포화
- 프로세스 정보 접근 거부

애플리케이션 로그는 파일로 기록한다.

```text
logs/network-monitor.log
```

로그 로테이션을 적용한다.

- 파일당 최대 10MB
- 최대 5개 유지

---

## 21. 보안 및 개인정보 고려사항

- 패킷 캡처는 민감한 메타데이터를 포함할 수 있다.
- 원본 payload는 기본적으로 저장하지 않는다.
- 저장 경로를 사용자에게 명확히 표시한다.
- 로그 내보내기 전 개인정보 포함 가능성을 안내한다.
- 애플리케이션이 사용자 모르게 네트워크 데이터를 외부로 전송하지 않아야 한다.
- 자동 업로드나 원격 분석 기능은 구현하지 않는다.
- 관리자 권한은 필요한 기능에만 사용한다.

---

## 22. 성능 요구사항

MVP 성능 목표:

- GUI 응답 유지: 일반적인 트래픽에서 UI 프리징 없음
- 화면 로그 최대 행 수: 기본 10,000행
- UI 갱신 간격: 250ms 이상
- 그래프 갱신 간격: 500ms 이상
- 메모리 사용량: 장시간 실행 시 지속 증가하지 않음
- 큐 포화 상태에서 애플리케이션 중단 없음
- 캡처 중지 후 관련 스레드 정상 종료

성능 측정 항목:

- 초당 캡처 패킷 수
- 초당 처리 패킷 수
- 큐 크기
- 드롭 패킷 수
- UI 업데이트 처리 시간
- 메모리 사용량
- CPU 사용량

---

## 23. 설정 항목

설정 파일 예시:

```toml
[capture]
default_interface = ""
bpf_filter = "ip or ip6"
queue_size = 50000
store_raw_payload = false

[ui]
refresh_interval_ms = 250
chart_interval_ms = 1000
max_visible_rows = 10000
auto_scroll = true

[storage]
enable_sqlite = false
database_path = "./data/traffic.db"
batch_size = 100
flush_interval_ms = 1000

[logging]
level = "INFO"
file_path = "./logs/network-monitor.log"
```

---

## 24. 개발 단계

## Phase 1. 프로젝트 초기화

- Python 프로젝트 생성
- PySide6 설치
- Ruff 설정
- mypy 설정
- pytest 설정
- 기본 로깅 설정
- 기본 메인 윈도우 생성

완료 조건:

- 애플리케이션이 실행된다.
- 빈 메인 화면이 표시된다.
- 테스트와 린터 명령이 실행된다.

## Phase 2. 네트워크 인터페이스 조회

- 인터페이스 목록 조회
- 인터페이스 이름과 IP 주소 표시
- 새로고침 기능
- 기본 인터페이스 자동 선택

완료 조건:

- Wi-Fi와 Ethernet 인터페이스가 목록에 표시된다.
- 인터페이스 선택 상태가 유지된다.

## Phase 3. 패킷 캡처

- Scapy AsyncSniffer 적용
- 캡처 시작 및 중지
- bounded queue 적용
- 드롭 패킷 카운터 구현

완료 조건:

- 선택한 인터페이스에서 패킷을 수신한다.
- 시작 및 중지를 반복해도 예외가 발생하지 않는다.
- UI가 멈추지 않는다.

## Phase 4. 패킷 파싱

- IPv4 및 IPv6 파싱
- TCP 및 UDP 파싱
- DNS 및 ICMP 파싱
- 방향 판별
- PacketRecord 생성

완료 조건:

- 샘플 패킷 테스트가 통과한다.
- 출발지, 목적지, 포트, 프로토콜이 정상 표시된다.

## Phase 5. 상세 로그 테이블

- QAbstractTableModel 구현
- QTableView 연결
- 배치 추가
- 최대 행 수 제한
- 자동 스크롤

완료 조건:

- 실시간 로그가 표시된다.
- 10,000행 이상 누적되어도 UI가 정상 동작한다.
- 오래된 로그가 자동 제거된다.

## Phase 6. 요약 패널 및 그래프

- 다운로드 및 업로드 속도 계산
- 누적 트래픽 계산
- 프로토콜 카운트
- pyqtgraph 적용
- 최근 60초 그래프

완료 조건:

- 실시간 속도와 그래프가 갱신된다.
- 캡처 중지 시 그래프 갱신도 중지된다.

## Phase 7. 필터

- 프로토콜 필터
- 방향 필터
- IP 및 포트 검색
- 프로세스 검색
- 화면 필터와 캡처 필터 구분

완료 조건:

- 필터 변경 시 화면 결과가 즉시 갱신된다.
- 원본 로그 데이터는 유지된다.

## Phase 8. 프로세스 매핑

- psutil 연결 테이블 캐시
- PID 매핑
- 프로세스 이름 표시
- 접근 권한 예외 처리

완료 조건:

- 주요 TCP 연결에 프로세스 이름이 표시된다.
- 매핑하지 못한 경우 빈 값 또는 Unknown으로 표시된다.

## Phase 9. 저장 및 내보내기

- SQLite 저장
- CSV 내보내기
- JSON Lines 내보내기
- 저장 워커
- 배치 insert

완료 조건:

- 캡처 중 UI 지연 없이 저장된다.
- 저장한 파일을 다시 열어 데이터를 확인할 수 있다.

## Phase 10. 안정화 및 패키징

- 관리자 권한 처리
- Npcap 검사
- 오류 메시지 개선
- PyInstaller 빌드
- 장시간 실행 테스트
- 메모리 누수 점검

완료 조건:

- Windows 실행 파일을 생성할 수 있다.
- Npcap 미설치 시 설치 안내가 표시된다.
- 2시간 이상 실행 시 메모리가 비정상적으로 증가하지 않는다.

---

## 25. 테스트 요구사항

### 25.1 단위 테스트

- IPv4 패킷 파싱
- IPv6 패킷 파싱
- TCP 패킷 파싱
- UDP 패킷 파싱
- DNS 패킷 파싱
- ICMP 패킷 파싱
- 송수신 방향 판별
- 속도 계산
- 단위 변환
- 링 버퍼 행 제한
- 필터 조건

### 25.2 통합 테스트

- 캡처 시작 및 중지
- 캡처 큐 포화
- 파서 워커 종료
- SQLite 배치 저장
- UI 모델 배치 추가
- 인터페이스 변경
- 애플리케이션 종료 시 스레드 정리

### 25.3 수동 테스트

- Wi-Fi 캡처
- Ethernet 캡처
- VPN 활성화 상태
- 대용량 다운로드
- 대용량 업로드
- DNS 요청
- 브라우저 HTTPS 요청
- Docker 또는 WSL 네트워크
- 관리자 권한 없음
- Npcap 미설치

---

## 26. 코딩 규칙

- 모든 공개 함수와 클래스에 타입 힌트를 작성한다.
- 가능한 경우 `dataclass(slots=True)`를 사용한다.
- UI 코드와 비즈니스 로직을 분리한다.
- 전역 mutable state 사용을 피한다.
- 긴 작업은 UI 스레드에서 실행하지 않는다.
- 예외를 무시하지 않고 로그에 기록한다.
- 네트워크 관련 상수는 config 모듈에 둔다.
- 클래스당 책임을 하나로 제한한다.
- 함수는 가능하면 30줄 이내로 유지한다.
- 순환 import를 피한다.
- `ruff check`, `ruff format`, `mypy`, `pytest`를 통과해야 한다.

---

## 27. Claude Code 작업 지침

Claude Code는 다음 원칙에 따라 작업한다.

1. 한 번에 전체 기능을 구현하지 말고 Phase 단위로 작업한다.
2. 각 Phase 시작 전에 변경 파일 목록과 구현 계획을 먼저 제시한다.
3. 기존 구조를 확인한 후 최소 범위로 변경한다.
4. UI 스레드에서 캡처, 파싱, 저장을 실행하지 않는다.
5. `QTableWidget` 대신 `QTableView`와 `QAbstractTableModel`을 사용한다.
6. 패킷마다 Qt Signal을 보내지 않는다.
7. 패킷 캡처 큐에는 최대 크기를 지정한다.
8. UI에는 로그를 배치 단위로 반영한다.
9. 테스트 가능한 로직은 UI 클래스 밖으로 분리한다.
10. 작업 후 관련 테스트를 실행한다.
11. 실행하지 못한 테스트가 있다면 이유를 명시한다.
12. 외부 패키지를 추가하기 전에 필요성과 대안을 설명한다.
13. Windows 전용 로직은 별도 모듈에 격리한다.
14. 기존 기능을 깨뜨리지 않도록 작은 단위로 커밋 가능한 변경을 만든다.
15. 성능에 영향을 주는 부분에는 간단한 계측 로그를 추가한다.

---

## 28. Claude Code 초기 요청문

아래 요청문을 Claude Code에 전달하여 개발을 시작한다.

```text
이 저장소에 Python 3.12와 PySide6 기반의 Windows 실시간 네트워크 트래픽 모니터를 구현해 주세요.

먼저 현재 저장소 구조를 분석하고, 이 문서의 Phase 1만 구현하세요.

필수 조건:
- src 레이아웃을 사용합니다.
- 패키지 이름은 network_monitor로 합니다.
- PySide6 기반 기본 MainWindow를 만듭니다.
- 왼쪽 요약 패널과 오른쪽 상세 로그 패널을 QSplitter로 나눕니다.
- 오른쪽 로그 영역은 QTableView를 사용합니다.
- 기본 QAbstractTableModel을 별도 파일에 구현합니다.
- Ruff, mypy, pytest 설정을 추가합니다.
- Python logging 기반 파일 및 콘솔 로깅을 설정합니다.
- 애플리케이션 진입점은 python -m network_monitor.main으로 실행할 수 있어야 합니다.
- 아직 실제 패킷 캡처 기능은 구현하지 않습니다.
- 구현 후 실행 방법, 변경 파일, 테스트 결과를 정리해 주세요.

작업 전에 구현 계획과 변경 예정 파일을 먼저 제시하고, 이후 실제 파일을 수정하세요.
```

---

## 29. MVP 완료 기준

다음 조건을 모두 충족하면 MVP가 완료된 것으로 판단한다.

- 네트워크 인터페이스를 선택할 수 있다.
- 캡처를 시작하고 중지할 수 있다.
- TCP, UDP, DNS, ICMP 로그가 표시된다.
- 송신 및 수신 방향이 표시된다.
- 현재 업로드 및 다운로드 속도가 표시된다.
- 최근 60초 그래프가 표시된다.
- 상세 로그가 QTableView에 실시간으로 표시된다.
- 프로토콜, IP, 포트 필터가 동작한다.
- 화면에는 최대 10,000행만 유지된다.
- SQLite 또는 CSV 저장이 가능하다.
- 캡처 중에도 UI가 멈추지 않는다.
- 애플리케이션 종료 시 모든 워커가 정상 종료된다.
- Npcap 또는 권한 문제가 사용자에게 표시된다.
- 주요 파서와 집계 로직에 테스트가 있다.

---

## 30. 초기 범위에서 제외할 기능

다음 기능은 MVP에서 제외한다.

- HTTPS 요청 본문 복호화
- TLS 중간자 프록시
- 패킷 차단
- 패킷 수정 및 재주입
- 원격 트래픽 수집
- 클라우드 동기화
- 사용자 계정
- 자동 위협 차단
- 완전한 IDS 또는 IPS
- Wi-Fi 모니터 모드
- 다른 기기의 전체 트래픽 감청
- 커널 드라이버 자체 개발

---

## 31. 향후 확장 기능

- ETW 기반 정확한 프로세스 매핑
- 국가 및 ASN 정보 표시
- GeoIP 지도
- 비정상 트래픽 탐지
- 포트 스캔 탐지
- DNS 이상 탐지
- 연결 차단 기능
- WinDivert 연동
- PCAP 파일 열기 및 재생
- 세션 단위 분석
- TLS SNI 및 인증서 정보
- 플러그인 구조
- 다크 모드
- 시스템 트레이
- 백그라운드 캡처
- 알림 센터
- Rust 기반 고성능 캡처 엔진
