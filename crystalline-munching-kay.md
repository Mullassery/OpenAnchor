# IoT Learning Platform — Architecture Plan

## Context

Building a comprehensive, path-based IoT/cloud engineering learning platform covering the full stack: hardware sensors → ESP32/RPi → WiFi/BLE → MQTT → Kafka → PyFlink → storage.

**Primary audience: IT students with zero prior knowledge of cloud networking or IoT.** They may know basic computing concepts but cannot be assumed to know Linux, protocols, networking, or any hardware. Every topic must explain the "what" and "why" in plain language before any technical depth. No jargon without definition. Analogies over abstractions.

Secondary audiences (same platform, different entry paths): IoT/electronics enthusiasts learning data engineering and DevOps; data engineers/cloud devs learning hardware, protocols, and security.

**Hybrid Learning Model** (DataCamp-inspired):
- **Theoretical layer**: Knowledge graph, flashcards, conceptual quizzes (what → why)
- **Practical layer**: Hands-on labs with interactive code editors, terminals, sandboxed environments (how → practice)
- Example flow: Learn MQTT concept → take quiz → solve hands-on exercise (set up MQTT broker in Docker)

**Open Source Commitment**:
- **100% open source stack**: No proprietary tools, frameworks, or dependencies
- **Platform code**: Published as open source (GitHub, MIT license)
- **Infrastructure**: Self-hosted on open source infrastructure (Docker, Kubernetes)
- **No vendor lock-in**: Can be deployed anywhere by anyone

**Decisions confirmed**:
- Frontend: Next.js + React
- Backend: Rust (Axum)
- Content: MDX files + embedded lab definitions (YAML/JSON)
- **Database (Polyglot Persistence)**:
  - **PostgreSQL**: Transactional data (users, auth, enrollments, XP ledger, payment)
  - **MongoDB**: Flexible content (topics, labs, quiz attempts, user profiles, preferences)
  - **Neo4j** (v1.1+): Knowledge graph (prerequisite paths, recommendations, fastest traversals at scale)
- Auth: Required, full progress sync, Keycloak (open source OAuth2)
- MVP scope: Learning graph + quizzes + **basic hands-on labs** (not full simulation)
- UI/UX reference: DataCamp (three-pane layout: problem → suggestions → coding area)

---

## 1. Monorepo Structure

```
iot-learning-platform/
├── apps/
│   ├── web/                          # Next.js (App Router)
│   │   ├── app/
│   │   ├── components/
│   │   │   ├── graph/
│   │   │   ├── flashcards/
│   │   │   ├── quiz/
│   │   │   └── layout/
│   │   └── lib/
│   └── api/                          # Rust (Axum)
│       ├── src/
│       │   ├── main.rs
│       │   ├── routes/
│       │   ├── models/
│       │   ├── db/
│       │   └── graph/               # DAG traversal, lock/unlock, dagre layout
│       ├── Cargo.toml
│       └── migrations/              # sqlx migrations
├── content/
│   ├── topics/
│   │   ├── hardware/                # ESP32, Arduino, RPi, GPIO, AI HAT, sensors
│   │   ├── connectivity/            # WiFi, BLE, MQTT, CoAP, LoRaWAN, Modbus
│   │   ├── tools/                   # Node-RED, ModSim, MQTT Explorer, Grafana
│   │   ├── security/                # nmap, SSH, BLE security, WiFi sec, IEC 62443
│   │   ├── infrastructure/          # Docker, Ansible, CI/CD, OPC-UA, SCADA
│   │   └── data-pipeline/           # Kafka, PyFlink, TimescaleDB, InfluxDB
│   ├── paths/                       # YAML path definition files
│   └── schema/                      # JSON Schema for MDX frontmatter validation
├── packages/
│   ├── content-types/               # Shared TS types for MDX schema
│   └── graph-utils/                 # Graph traversal utilities (shared)
├── scripts/
│   ├── validate-content.ts          # CI: validate MDX frontmatter + cycle detection
│   ├── build-graph.ts               # Generate graph JSON from MDX
│   └── seed-topics.ts               # Seed DB from content (idempotent, uses content_hash)
├── docker/
│   ├── docker-compose.yml
│   └── Dockerfile.api
├── turbo.json
├── pnpm-workspace.yaml
└── CLAUDE.md
```

**Tooling**: Turborepo + pnpm workspaces. `cargo-chef` for Docker layer caching on the Rust API.

---

## 2. Learning Roadmap: From Foundations to Advanced AI/Vision

### **Strategic Vision: Build Solid Foundations for Advanced Topics**

The curriculum is structured in **layers**:
1. **Foundation Layer** (v1.0-v1.2): Linux, networks, security, microcontrollers, basic protocols
2. **Intermediate Layer** (v1.3-v2.0): IoT architectures, edge computing, data pipelines
3. **Advanced Layer** (v2.0+): OpenCV, Edge AI, ML models, computer vision on edge devices

**Future Advanced Topics** (built on solid foundations):
- **OpenCV**: Image processing, computer vision libraries (requires: Linux, Python, microcontrollers)
- **Edge AI**: Running ML models on edge devices (requires: Linux, microcontrollers, data pipelines)
- **Edge Computing**: Processing at the edge vs cloud (requires: networking, microcontrollers, security)
- **Specialized ML**: TensorFlow Lite, ONNX for edge (requires: Python, data pipeline knowledge)

**Why foundations matter**:
- Can't run OpenCV without understanding Linux file systems
- Can't deploy Edge AI without understanding microcontroller constraints
- Can't secure edge devices without firewall/networking knowledge
- Can't optimize data pipelines without understanding network protocols

---

## 2b. Living Curriculum Model

### **Philosophy: Courses Evolve, Pattern Stays Constant**

The syllabus is **not frozen** — it reflects industry best practices and market demand and is continuously updated. However, the underlying **pattern** remains constant.

**Pattern (Unchanging)**:
- Every topic follows the same structure: intro → flashcards → quiz → labs (optional) → unlock next
- Every topic has prerequisites and unlocks (DAG structure)
- Every topic teaches security aspects in context
- Every topic should take 20-30 minutes
- Every quiz has 5-8 questions with teaching explanations
- Every lab follows the three-pane DataCamp layout

**Content (Constantly Evolving)**:
- Topics added/removed based on market demand and industry trends
- Prerequisites can be reordered/updated as ecosystem matures
- New protocols, tools, frameworks added as they become industry standard
- Topics can be split (if too long) or merged (if closely related)
- Difficulty ratings adjusted based on learner feedback

**Example Evolution Timeline**:
- **v1.0** (Launch): Linux fundamentals, MQTT, Docker, PyFlink basics
- **v1.1** (Q2 2026)**: Full curriculum (83 topics)
- **v1.2** (Q3 2026): Add "Kubernetes Security" (new industry focus)
- **v1.3** (Q4 2026): Remove deprecated LoRaWAN topic, add 5G-NR
- **v2.0** (2027): Restructure data-pipeline category based on market shifts

**Implementation**:
- Topics stored in MongoDB (flexible schema allows updates)
- Content versioning (can see old versions, track changes)
- Prerequisite graph in Neo4j (can be reordered without breaking existing progress)
- No hard-coded topic IDs in code (dynamic loading from database)
- CI/CD validates new topics follow the pattern

---

## 3. Hands-On Labs Architecture (DataCamp Model)

### Lab Types & Execution Environments

**Lab Type 1: Linux Terminal Labs** (nmap, SSH, bash scripting, Docker, Ansible)
- **Environment**: Containerized Linux shell (Docker) with pre-configured tools
- **Execution**: User runs real commands (`nmap localhost`, `docker ps`, `ssh user@host`)
- **Grading**: Test output against expected results (e.g., "find 3 open ports" → parse nmap output)
- **Sandbox**: Resource limits (CPU, memory, network) + whitelist-only outbound connections
- **Examples**: "Scan your local network with nmap and identify open ports" → provides `nmap localhost`, expects user to add flags

**Lab Type 2: Code Sandbox Labs** (PyFlink, Python scripts, YAML configs)
- **Environment**: Docker container with Python + Kafka + PyFlink pre-installed
- **Execution**: User writes PyFlink streaming job; backend executes it against mock data
- **Grading**: Check output (aggregated results, window calculations) against expected
- **Examples**: "Write a PyFlink windowing job to aggregate MQTT sensor readings" → template + code editor

**Lab Type 3: Interactive Network Labs** (AWS VPC, VLAN simulation)
- **Environment**: Terraform-provisioned AWS sandbox or local emulation (Mininet for network simulation)
- **Execution**: User modifies Terraform or Mininet config; backend applies changes
- **Grading**: Verify network connectivity, subnet routing, security group rules
- **Examples**: "Create a VPC with public/private subnets and verify routing" → Terraform template + guided exercise

**Lab Type 4: Configuration Labs** (Docker Compose, Ansible, Node-RED)
- **Environment**: Editor for declarative configs (YAML, JSON)
- **Execution**: Backend validates and applies (Docker Compose up, Ansible playbook run)
- **Grading**: Check service status, logs, endpoints
- **Examples**: "Write Docker Compose to run MQTT broker + Telegraf + InfluxDB" → template + test suite

### Three-Pane UI Layout (DataCamp Reference)

```
┌─────────────────────────────────────────────────────────┐
│ LearnDataFlow: Linux Terminal Fundamentals - Lab 3      │
├──────────────────────────┬──────────────────────────────┤
│                          │                              │
│  PROBLEM AREA            │  CODING AREA                 │
│  ───────────────         │  ────────────                │
│  • Problem statement:     │  $ ▮                         │
│    "Use ls to list      │  [Terminal emulator]         │
│    files in /tmp"       │                              │
│                          │                              │
│  • Expected output:      │  $ ls -la /tmp               │
│    (shows example)       │  total 48                    │
│                          │  drwxrwxrwt  10 root  ...   │
│  • Hints:                │                              │
│    "Try adding the -la   │                              │
│     flags for detailed"  │                              │
│  [Show solution toggle]  │                              │
│                          │                              │
└──────────────────────────┴──────────────────────────────┘
│ SUGGESTION AREA / CONTEXT                               │
├─────────────────────────────────────────────────────────┤
│ 📚 Concept: ls lists directory contents. Flags modify  │
│    output. -l = long format, -a = show hidden files     │
│ 💡 Hint: Type "man ls" in terminal to see all flags    │
│ ✓ Test: When you're done, your output will match ↑     │
└─────────────────────────────────────────────────────────┘
```

### Content Schema for Labs

```yaml
# Inside topic frontmatter
labs:
  - id: "lab-mqtt-setup"
    title: "Set Up MQTT Broker with Docker"
    type: "docker-compose"
    difficulty: 1
    estimatedMinutes: 15
    
    # Problem statement (left pane)
    problemStatement: |
      You need to run an MQTT broker locally for testing.
      Write a Docker Compose file that:
      1. Runs the Mosquitto MQTT broker
      2. Exposes port 1883 (MQTT default)
      3. Mounts a config file
    
    # Template (what user starts with)
    template: |
      version: '3'
      services:
        mosquitto:
          image: ____
          ports:
            - "____:1883"
          volumes:
            - ____
    
    # Test cases (what grader checks)
    tests:
      - name: "Docker Compose syntax valid"
        command: "docker-compose config"
        expectedExitCode: 0
      - name: "Mosquitto container starts"
        command: "docker-compose up -d && sleep 3 && docker-compose ps"
        expectedOutput: "mosquitto.*running"
    
    # Hints (context pane)
    hints:
      - level: 1
        text: "Mosquitto image is 'eclipse-mosquitto'"
      - level: 2
        text: "Volume mapping syntax: ./mosquitto.conf:/mosquitto/config/mosquitto.conf"
    
    solution: |
      version: '3'
      services:
        mosquitto:
          image: eclipse-mosquitto
          ports:
            - "1883:1883"
          volumes:
            - ./mosquitto.conf:/mosquitto/config/mosquitto.conf
```

---

## 3. Full Syllabus (Knowledge Graph Topics)

Aligned with **IIoT standards**: IEC 62443, IEC 61850, OPC-UA, MQTT v5, Industry 4.0.

### Path A: IoT/Hardware → Cloud (for electronics/IoT enthusiasts)
Entry at hardware fundamentals, graduates to data pipelines.

### Path B: Cloud/Data → IoT (for data engineers/cloud devs)
Entry at MQTT/Kafka, graduates to hardware understanding and security.

### Path C: Security Specialist
Entry at network scanning, spans all layers.

---

### Category 0: Linux Fundamentals (MANDATORY — universal prerequisite for ALL paths)
Every user completes this block before any path unlocks. No exceptions.

| id | Title | Prerequisites |
|---|---|---|
| linux-terminal-basics | Linux Terminal Basics (ls, cd, pwd, mkdir) | — |
| linux-file-permissions | File Permissions (chmod, chown, sudo) | linux-terminal-basics |
| linux-processes | Processes and Services (ps, top, systemctl, kill) | linux-terminal-basics |
| linux-package-mgmt | Package Management (apt, yum, snap) | linux-terminal-basics |
| linux-networking-cmds | Networking Commands (ping, ip addr, ss, netstat, curl) | linux-terminal-basics |
| linux-text-tools | Text Tools (grep, awk, sed, cat, less, tail -f) | linux-terminal-basics |
| linux-bash-scripting | Bash Scripting Basics | linux-file-permissions |
| linux-ssh-basics | SSH Basics (keys, config, scp) | linux-networking-cmds |

All 8 must be completed before path selection unlocks any category-specific topics. This ensures every learner has the command-line foundation to run Docker, test MQTT, scan with nmap, and configure cloud VMs.

---

### Category 1: Hardware & Embedded Systems (16 topics)
| id | Title | Prerequisites |
|---|---|---|
| what-is-microcontroller | What is a Microcontroller? | — |
| arduino-basics | Arduino Basics | what-is-microcontroller |
| esp32-intro | ESP32 Introduction | arduino-basics |
| gpio-fundamentals | GPIO: General Purpose I/O | esp32-intro |
| analog-digital-sensors | Analog vs Digital Sensors | gpio-fundamentals |
| common-sensors | Common IoT Sensors (temp, humidity, motion) | analog-digital-sensors |
| i2c-spi-protocols | I2C and SPI Protocols | gpio-fundamentals |
| raspberry-pi-intro | Raspberry Pi Introduction | what-is-microcontroller |
| rpi-gpio | Raspberry Pi GPIO | raspberry-pi-intro |
| rpi-ai-hat | Raspberry Pi AI HAT | raspberry-pi-intro |
| edge-compute-basics | Edge Computing Basics | esp32-intro, raspberry-pi-intro |
| power-management | IoT Power Management | esp32-intro |
| firmware-basics | Firmware and Flashing | esp32-intro |
| pcb-basics | PCB Design Basics | arduino-basics |
| ota-updates | OTA (Over-the-Air) Updates | firmware-basics |
| digital-twins | Digital Twins Concept | edge-compute-basics |

### Category 2: Connectivity & Protocols (14 topics)
| id | Title | Prerequisites |
|---|---|---|
| wifi-basics | WiFi Fundamentals | esp32-intro |
| ble-basics | Bluetooth Low Energy (BLE) | esp32-intro |
| mqtt-protocol | MQTT Protocol | wifi-basics |
| mqtt-v5-features | MQTT v5 New Features | mqtt-protocol |
| coap-protocol | CoAP Protocol | wifi-basics |
| lorawan-basics | LoRaWAN Basics | wifi-basics |
| http-rest-iot | HTTP/REST from IoT Devices | wifi-basics |
| modbus-rtu-tcp | Modbus RTU/TCP | what-is-microcontroller |
| opc-ua-intro | OPC-UA Introduction | modbus-rtu-tcp |
| dnp3-intro | DNP3 Protocol | modbus-rtu-tcp |
| mqtt-kafka-bridge | MQTT to Kafka Bridge | mqtt-protocol, kafka-basics |
| edge-to-cloud-patterns | Edge-to-Cloud Patterns | mqtt-protocol, edge-compute-basics |
| time-sync-ntp | Time Synchronization (NTP/PTP) | wifi-basics |
| 5g-nb-iot | 5G and NB-IoT for IIoT | lorawan-basics |

### Category 3: Tools (Hands-On Software) (10 topics)
| id | Title | Prerequisites |
|---|---|---|
| mqtt-explorer | MQTT Explorer | mqtt-protocol |
| node-red-intro | Node-RED Introduction | mqtt-protocol |
| node-red-flows | Node-RED Flows and Nodes | node-red-intro |
| node-red-security | Securing Node-RED | node-red-flows, docker-basics |
| modsim-intro | ModSim: Modbus Simulator | modbus-rtu-tcp |
| grafana-basics | Grafana Dashboards | docker-basics |
| grafana-iot | Grafana for IoT Metrics | grafana-basics, influxdb-basics |
| kafka-ui-tools | Kafka UI Tools (Kafdrop, AKHQ) | kafka-basics |
| wireshark-iot | Wireshark for IoT Traffic | wifi-basics |
| scada-hmi-intro | SCADA and HMI Introduction | opc-ua-intro |

### Category 4: Security (15 topics)
| id | Title | Prerequisites |
|---|---|---|
| iot-attack-surface | IoT Attack Surface | wifi-basics |
| nmap-basics | nmap: Network Scanning | iot-attack-surface |
| nmap-advanced | nmap Advanced Techniques | nmap-basics |
| ssh-basics | SSH: Secure Remote Access | wifi-basics |
| ssh-hardening | SSH Key Management and Hardening | ssh-basics |
| wifi-security | WiFi Security (WPA3, rogue APs) | wifi-basics, nmap-basics |
| ble-security | BLE Security and Attacks | ble-basics, iot-attack-surface |
| mqtt-security | MQTT Security (TLS, Auth, ACLs) | mqtt-protocol, ssh-basics |
| tls-mtls-iot | TLS/mTLS for IoT Devices | firmware-basics |
| firmware-security | Firmware Security and CVEs | firmware-basics, iot-attack-surface |
| iec-62443 | IEC 62443 Industrial Security Standard | iot-attack-surface |
| owasp-iot-top10 | OWASP IoT Top 10 | iot-attack-surface |
| zero-trust-iot | Zero Trust for IoT | owasp-iot-top10 |
| devsecops-iot | DevSecOps for IoT | iec-62443, docker-security |
| incident-response | IoT Incident Response | zero-trust-iot |

### Category 5: Infrastructure & DevOps (12 topics)
| id | Title | Prerequisites |
|---|---|---|
| docker-basics | Docker Basics | — |
| docker-compose | Docker Compose | docker-basics |
| docker-security | Docker Container Security | docker-compose |
| ansible-basics | Ansible Basics | ssh-basics, docker-basics |
| ansible-iot | Ansible for IoT Device Provisioning | ansible-basics |
| ansible-playbooks | Writing Ansible Playbooks | ansible-basics |
| cicd-iot | CI/CD for IoT Firmware | ansible-basics, ota-updates |
| kubernetes-edge | Kubernetes at the Edge (K3s) | docker-compose |
| aws-iot-core | AWS IoT Core | mqtt-protocol, docker-basics |
| azure-iot-hub | Azure IoT Hub | mqtt-protocol, docker-basics |
| greengrass-edge | AWS Greengrass Edge Runtime | aws-iot-core, edge-compute-basics |
| terraform-iot | Infrastructure as Code (Terraform) | aws-iot-core |

### Category 6: Data Pipeline & Engineering (18 topics)
| id | Title | Prerequisites |
|---|---|---|
| kafka-basics | Apache Kafka Basics | docker-basics |
| kafka-topics-partitions | Kafka Topics and Partitions | kafka-basics |
| kafka-producers-consumers | Kafka Producers and Consumers | kafka-topics-partitions |
| kafka-streams | Kafka Streams Basics | kafka-producers-consumers |
| kafka-security | Kafka Security (SASL, TLS, ACLs) | kafka-basics, tls-mtls-iot |
| pyflink-intro | PyFlink Introduction | kafka-basics |
| pyflink-streaming | PyFlink Streaming Aggregations | pyflink-intro |
| pyflink-windowing | Windowing in PyFlink | pyflink-streaming |
| pyflink-stateful | Stateful Processing in PyFlink | pyflink-windowing |
| influxdb-basics | InfluxDB for Time-Series Data | docker-basics |
| telegraf-intro | Telegraf: Data Collection Agent | influxdb-basics |
| telegraf-plugins | Telegraf Input/Output Plugins | telegraf-intro |
| timescaledb-basics | TimescaleDB Basics | docker-basics |
| data-lake-iot | Data Lake Patterns for IoT | kafka-basics |
| stream-batch-lambda | Lambda Architecture (Stream + Batch) | pyflink-streaming |
| data-quality-iot | Data Quality in IoT Pipelines | pyflink-streaming |
| schema-registry | Schema Registry (Avro/Protobuf) | kafka-producers-consumers |
| opentelemetry-iot | OpenTelemetry for IoT Observability | grafana-iot, kafka-basics |

### Category 7: Cloud Networking & Infrastructure (14 topics)
Each topic includes: setup → security testing commands (ping, traceroute, nmap, curl, aws/az/gcloud CLI).

| id | Title | Prerequisites |
|---|---|---|
| cloud-networking-basics | Cloud Networking Fundamentals | linux-networking-cmds |
| aws-vpc-setup | AWS VPC: Subnets, Route Tables, IGW | cloud-networking-basics |
| aws-vpc-security | AWS Security Groups and NACLs | aws-vpc-setup |
| aws-vpc-testing | Testing AWS VPC with CLI commands | aws-vpc-security |
| azure-vnet-setup | Azure VNet and Subnets | cloud-networking-basics |
| azure-vnet-security | Azure NSGs and Firewall Rules | azure-vnet-setup |
| gcp-vpc-setup | GCP VPC and Subnet Design | cloud-networking-basics |
| vlan-basics | VLAN Fundamentals | cloud-networking-basics |
| vlan-iot-segmentation | VLAN Segmentation for IoT Security | vlan-basics, iec-62443 |
| vpn-site-to-site | Site-to-Site VPN for IoT | aws-vpc-security, linux-ssh-basics |
| private-link-endpoints | AWS PrivateLink / Azure Private Endpoints | aws-vpc-security |
| cloud-iot-ingestion | Cloud IoT Ingestion Patterns (IoT Core, IoT Hub) | aws-vpc-setup, mqtt-protocol |
| network-monitoring-cloud | Cloud Network Monitoring (VPC Flow Logs) | aws-vpc-testing |
| zero-trust-networking | Zero Trust Network Access (ZTNA) | vlan-iot-segmentation, zero-trust-iot |

**Total: 91 topics across 7 categories + 8 Linux fundamentals**

---

### Design Principle 1: Security-at-Each-Phase

Security is **not a separate track** — it is woven into every category. Each topic's quiz includes at least one security-oriented question. Topics with a `securityFocus` flag in frontmatter trigger a security callout panel in the UI ("Security note: when deploying this in production, watch for..."). Examples:

- `kafka-basics` → "What happens if Kafka has no authentication?" (lateral link to `kafka-security`)
- `aws-vpc-setup` → "What default rule allows all inbound traffic and why is that dangerous?"
- `docker-basics` → "What is the security risk of running containers as root?"
- `node-red-flows` → "Node-RED has a web UI — what should you do before exposing it?"
- `influxdb-basics` → "InfluxDB's default config disables auth — what are the implications?"

This ensures learners build security awareness naturally, not as an afterthought.

### Design Principle 2: Gamification & Engagement (Low Friction)

**Core philosophy**: Celebrate progress, not perfection. Make completion easy; mastery optional.

**Gamification Elements:**

1. **XP (Experience Points)** — Earned for actions, not gate-keeping
   - Start quiz: +5 XP
   - Complete flashcard deck: +10 XP
   - Answer quiz question: +2 XP (correct) or +1 XP (incorrect)
   - Complete lab: +20 XP
   - View solution/hint: +0 XP (no penalty for asking for help)
   - Total per topic: ~50-100 XP

2. **Streaks** — Consecutive days of learning
   - 1 day: "You're on a roll 🔥"
   - 7 days: Bronze streak (visual badge)
   - 30 days: Silver streak + small reward (certificate, unlock exclusive topic)
   - 100 days: Gold streak + major reward (leaderboard feature, profile badge)
   - **No penalty for breaking streak** (compassionate design: "Streak reset. No worries—pick up where you left off")

3. **Badges** — Achievements for milestones (not required for progression)
   - "Linux Fundamentals Complete" (complete all 8 Linux topics)
   - "Security Awareness" (complete 3 security-focused topics)
   - "IoT Practitioner" (complete 20 topics across all categories)
   - "Lab Solver" (complete 10 hands-on labs)
   - "Helpful Learner" (share 5 study notes or tips with community)
   - **Badges appear on user profile, shareable on social media**

4. **Levels/Tiers** — Visual progression system
   - Level 1: Novice (0-500 XP)
   - Level 2: Apprentice (500-1,500 XP)
   - Level 3: Practitioner (1,500-3,500 XP)
   - Level 4: Expert (3,500-7,000 XP)
   - Level 5: Master (7,000+ XP)
   - **Tier unlocks**: At Level 2, unlock "Study Groups" feature; at Level 3, unlock ability to create custom learning paths

5. **Daily/Weekly Challenges** — Bite-sized optional quests
   - "Complete a Linux lab today" (+25 bonus XP)
   - "Master a new protocol this week" (+50 bonus XP)
   - "Complete 3 labs in 3 days" (+100 bonus XP)
   - Challenges rotate; optional, never blocking progress

6. **Skill Trees (Visual Path Map)** — See your journey
   - Animated progress toward completing each category
   - "You've completed 3/8 Linux fundamentals"
   - Visual tree showing unlocked → in-progress → locked topics
   - Milestone celebrations: "You've completed 25% of IoT Hardware fundamentals! 🎉"

7. **Completion Multipliers** — Easy wins
   - **Quiz completion**: Only need 50%+ to "pass" and unlock next topics (not 60%+)
   - **Lab completion**: First test pass = "good enough"; no required perfection
   - **Multiple paths to completion**: User can do either quiz OR lab (not both) to complete a topic
   - **Flexible prerequisites**: At 70% progress, user can attempt next topic (not 100% requirement)

8. **Certificates & Credentials**
   - "Linux Fundamentals Certificate" — print-friendly, shareable on LinkedIn
   - "IoT Hardware Specialist" — after completing hardware category + 5 labs
   - "Full Stack IoT Engineer" — after completing all 91 topics
   - Certificates show: date earned, XP at time of completion, topics covered
   - Blockchain-verified (optional, v1.1+): QR code to verify credential

9. **Leaderboards (Optional, Opt-In)**
   - **Global XP leaderboard** (top 100 learners this month) — opt-in to appear
   - **Cohort leaderboards** (students in same university/company) — visibility controlled
   - **No shame in not appearing** (default: private profile)
   - Leaderboard sorts by: XP, streaks, badges, topics completed (user chooses)

10. **Profile & Social Sharing**
    - Public learner profile: badges, current streak, topics completed, recent achievements
    - Share achievements: "I completed Linux Fundamentals 🎓" → Twitter/LinkedIn card
    - "Study buddy" feature: invite friends, see their progress (optional)
    - Cohort/class dashboards (for instructors)

---

### Design Principle 3: Ease of Level Completion

**Barrier-free progression:**

| Gate Type | Traditional Approach | LearnDataFlow Approach |
|-----------|---------------------|----------------------|
| **Quiz pass threshold** | 80% required | 50% required (understanding > perfection) |
| **Lab completion** | All tests must pass | First test pass = complete (can review solution for others) |
| **Prerequisites** | Hard gate (100% complete) | Flexible (70% complete allows attempt at next) |
| **Progression path** | Linear only | Multiple paths: quiz OR lab (pick your mode) |
| **Failure handling** | Quiz failed? Retry 3x then blocked | Quiz failed? See explanation, review flashcards, try whenever ready |
| **Time limits** | Timed quizzes/labs | No time limits (focus on learning, not speed) |
| **Perfection requirement** | Must master every topic | Can move forward with "working knowledge"; revisit anytime |

**Example flow: User completes "MQTT Protocol" topic**
1. Reads intro (1 min) → +5 XP
2. Reviews flashcards (5 min) → +10 XP
3. Takes quiz (7 min, gets 4/8 correct = 50%)
   - Shows explanation for each answer
   - Score: 50% (below typical 60-70% threshold, but OK here)
   - Suggestion: "You got the basics! Review flashcards on [concepts], then try again or move forward."
4. User chooses: Retake quiz OR Attempt lab OR Move to next topic
   - **Option A**: Retake quiz (same questions, different order) → earn +5 bonus XP on perfect score
   - **Option B**: Complete "Set up MQTT broker in Docker" lab → +20 XP + badge "MQTT Practitioner"
   - **Option C**: Move forward to "MQTT v5 Features" (next topic unlocks) → topics marked as "completed with 50%"
5. User clicks "Next" → Unlock animation, +10 XP for level milestone, new topic available
6. Daily notification: "You're on a 3-day streak! Complete one more topic to reach 7 days 🔥"

---



Critical concepts appear repeatedly in different contexts to reinforce mastery through **spaced repetition and interleaving**:

**Example: "Containerization" reinforced across 5+ topics:**
- `docker-basics` — "What is a container?" (foundational)
- `docker-compose` — "Use containers to run multiple services"
- `node-red-security` — "Run Node-RED in a container for isolation" (security context)
- `ansible-iot` — "Deploy containerized services via Ansible" (DevOps context)
- `kubernetes-edge` — "Orchestrate containers at the edge" (scaling context)
- `cicd-iot` — "Build and push Docker images in CI/CD pipeline" (automation context)

**Example: "Authentication" reinforced across 6+ topics:**
- `ssh-basics` — "SSH key-based auth for remote access"
- `mqtt-security` — "MQTT client certificates and username/password"
- `kafka-security` — "Kafka SASL/TLS authentication"
- `aws-vpc-security` — "AWS IAM roles and security groups"
- `tls-mtls-iot` — "mTLS mutual authentication between devices and cloud"
- `zero-trust-iot` — "Identity-first security model"

**Implementation:**
- Add `reinforces: [topic_id, topic_id, ...]` to frontmatter (links to earlier concepts being reinforced)
- Add `reinforced_by: [topic_id, topic_id, ...]` (topics that build on this)
- UI shows: "You learned this concept in [topic]. Here it appears again in [new context]."
- Spaced repetition algorithm suggests revisiting foundational topics when reinforcement topics unlock
- Labs that build on earlier topics reference prior labs: "Like in the Docker Compose lab, here you'll again use containers..."

This ensures **deep learning through repetition in varied contexts**, not one-shot memorization.

---

## 3. Content Schema (MDX Frontmatter)

Every topic is a single `.mdx` file. MDX body = introduction page. Frontmatter = machine-readable contract.

```yaml
---
id: "kafka-basics"
slug: "kafka-basics"
title: "Apache Kafka Basics"
description: "Message brokers and publish-subscribe for IoT data streams"
category: "data-pipeline"
difficulty: 2                  # 1=beginner, 2=intermediate, 3=advanced, 4=expert
estimatedMinutes: 25
iiotStandard: ""               # optional: e.g. "IEC 62443", "OPC-UA", "MQTT v5"
paths:
  - "data-engineer-to-iot"
  - "full-stack-iot"
prerequisites:
  - "docker-basics"
  - "mqtt-protocol"
unlocks:
  - "kafka-topics-partitions"
  - "mqtt-kafka-bridge"
lateralLinks:
  - "timescaledb-basics"       # non-blocking, sidebar suggestions
flashcards:
  - front: "What problem does Kafka solve?"
    back: "Decouples producers from consumers. Buffers IoT ingestion spikes without data loss."
  - front: "What is a Kafka topic?"
    back: "A named, ordered, append-only log. Producers write; multiple consumers read independently."
quiz:
  passingScore: 60
  questions:
    - id: "kbq1"
      stem: "An ESP32 publishes every 100ms. PyFlink processes every 5s. What prevents data loss?"
      options:
        - text: "Replication factor"
          correct: false
          explanation: "Replication protects against broker failure — not producer/consumer rate mismatch."
        - text: "Retention period"
          correct: true
          explanation: "Kafka retains records for a configurable duration. PyFlink reads at its own pace within that window."
        - text: "Consumer group offset"
          correct: false
          explanation: "Offsets track where a consumer has read to — they don't control retention or data survival."
        - text: "Partition count"
          correct: false
          explanation: "Partitions affect parallelism, not durability against rate mismatch."
---
```

**Content authoring constraints** (enforced via `CONTENT_GUIDE.md` and validated by `validate-content.ts`):
- Every topic intro must answer "what is this?" in one plain-English sentence before any technical detail
- No acronym used without expanding it on first use (e.g., "MQTT (Message Queuing Telemetry Transport)")
- Every flashcard `back` must use an analogy or real-world example alongside the technical definition
- Every wrong quiz answer needs a specific explanation addressing the misconception — not generic "that's wrong"
- Question stems must use concrete scenarios ("An ESP32 sensor publishes every 100ms...") not abstract theory
- Difficulty 1 topics must be readable by someone who has never opened a terminal

**Topic Length & Pacing Constraints** (prevent frustration, maintain engagement):
- **Intro page**: Max 500 words (2-3 min read). One key concept per topic, not broad surveys.
- **Flashcard deck**: 5-8 cards max (3-5 min to review). Use spaced repetition later for deep retention.
- **Quiz**: 5-8 questions max (7-10 min to complete). Stop before cognitive overload.
- **Lab**: 15-30 min max to complete (including hints). If it takes longer, break into 2 smaller labs.
- **Total topic time**: 20-30 min per topic (intro + flashcards + quiz OR lab). Not more.
- **Difficulty progression**: Each topic slightly harder than the last; no sudden jumps. Estimate difficulty delta: ≤ 0.5 points on 1-4 scale.

**Example: Good Topic Granularity**
- ❌ Bad: "AWS VPC Fundamentals" (covers VPC, subnets, route tables, security groups, NAT, VPN — 90 min)
- ✅ Good: Split into 4 topics (15 min each):
  1. "What is AWS VPC?"
  2. "Subnets and Route Tables"
  3. "Security Groups Explained"
  4. "NAT Gateways and VPNs"

This maintains **short, satisfying completion cycles**. Users see progress frequently (every 20-30 min), which keeps motivation high.

**Pacing signals in UI:**
- "This topic typically takes 25 minutes" (shown before starting)
- Progress bar shows estimated time remaining (updates as user completes sections)
- Celebration on completion: "You completed MQTT Protocol in 28 min! 🎉 Next topic starts in 5 min."

---

## 4. Polyglot Database Architecture

### **Database Distribution Strategy**

```
┌─────────────────────────────────────────────────────────┐
│                  LearnDataFlow Architecture              │
├──────────────────┬──────────────────┬──────────────────┤
│                  │                  │                  │
│  PostgreSQL      │   MongoDB        │   Neo4j          │
│  (Transactional) │   (Content)      │   (Graph)        │
│                  │                  │                  │
│ • Users          │ • Topics (MDX)   │ • Topic nodes    │
│ • Auth tokens    │ • Lab defs       │ • Prerequisites  │
│ • Enrollments    │ • Quiz attempts  │ • Reinforcements │
│ • XP ledger      │ • Profiles       │ • Paths          │
│ • Payments       │ • Preferences    │ • Recommendations│
│ • Gamification   │ • Bookmarks      │                  │
│ • Sessions       │                  │ (v1.1+)          │
│                  │                  │                  │
└──────────────────┴──────────────────┴──────────────────┘
        ↓                  ↓                   ↓
   ACID transactions   Schema flexibility   Graph queries
   (Strict data)       (Content changes)    (Traversals)
```

### **v1.0 Schema: PostgreSQL + MongoDB**

#### PostgreSQL (Transactional Core)
```sql
-- Users & Auth (No subscription/payment needed)
CREATE TABLE users (
    id              UUID PRIMARY KEY,
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT,  -- NULL if Google OAuth
    google_id       TEXT UNIQUE,  -- if using Google SSO
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Learning Path Enrollment (Free, auto-enrollment at signup)
CREATE TABLE user_paths (
    user_id         UUID NOT NULL REFERENCES users(id),
    path_id         TEXT NOT NULL,  -- 'iot-to-cloud', 'cloud-to-iot', 'security-specialist'
    enrolled_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at    TIMESTAMPTZ,  -- NULL until path is 100% complete
    PRIMARY KEY (user_id, path_id)
);

-- Gamification
CREATE TABLE user_gamification (
    user_id         UUID PRIMARY KEY REFERENCES users(id),
    total_xp        INTEGER NOT NULL DEFAULT 0,
    current_level   SMALLINT NOT NULL DEFAULT 1,
    current_streak  SMALLINT NOT NULL DEFAULT 0,
    longest_streak  SMALLINT NOT NULL DEFAULT 0,
    last_activity_date DATE NOT NULL DEFAULT CURRENT_DATE,
    badges          TEXT[] NOT NULL DEFAULT '{}',
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Progress Tracking (summary; detailed history in MongoDB)
CREATE TABLE user_progress (
    user_id         UUID NOT NULL REFERENCES users(id),
    topic_id        TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'available',
    xp_earned       SMALLINT NOT NULL DEFAULT 0,
    completed_at    TIMESTAMPTZ,
    last_viewed_at  TIMESTAMPTZ NOT NULL DEFAULT now(),  -- Track when they last studied this topic
    view_count      INTEGER NOT NULL DEFAULT 0,          -- How many times they've visited this topic
    quiz_attempts   INTEGER NOT NULL DEFAULT 0,
    lab_attempts    INTEGER NOT NULL DEFAULT 0,
    best_quiz_score SMALLINT,
    last_quiz_score SMALLINT,
    total_time_spent_seconds INTEGER NOT NULL DEFAULT 0, -- Cumulative time on this topic
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, topic_id)
);

-- XP Ledger (immutable, for auditing)
CREATE TABLE xp_ledger (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    amount          SMALLINT NOT NULL,
    reason          TEXT NOT NULL,  -- 'quiz_pass', 'lab_complete', 'streak', etc.
    topic_id        TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_user_progress_user ON user_progress(user_id);
CREATE INDEX idx_xp_ledger_user ON xp_ledger(user_id);
```

#### MongoDB (Flexible Content & Schema)
```javascript
// Topics Collection
db.topics.insertOne({
  _id: "mqtt-protocol",
  title: "MQTT Protocol",
  category: "connectivity",
  difficulty: 2,
  estimatedMinutes: 25,
  
  // Content
  intro: "MQTT is a publish-subscribe...",
  
  // Flashcards
  flashcards: [
    { front: "What is MQTT?", back: "..." },
    { front: "What is QoS?", back: "..." }
  ],
  
  // Quiz
  quiz: {
    passingScore: 50,
    questions: [
      {
        id: "q1",
        stem: "...",
        options: [
          { text: "...", correct: true, explanation: "..." },
          { text: "...", correct: false, explanation: "..." }
        ]
      }
    ]
  },
  
  // Labs (optional)
  labs: [
    {
      id: "lab-mqtt-setup",
      type: "docker-compose",
      problemStatement: "Set up MQTT broker...",
      template: "version: '3'...",
      tests: [{ name: "...", command: "..." }],
      hints: [{ level: 1, text: "..." }]
    }
  ],
  
  // Graph relationships (for v1.0, stored here; v1.1+ synced to Neo4j)
  prerequisites: ["wifi-basics"],
  unlocks: ["mqtt-v5-features"],
  reinforces: ["docker-basics"],  // where this concept reappears
  
  createdAt: ISODate("2025-01-01"),
  updatedAt: ISODate("2025-01-15")
});

// Quiz Attempts Collection (versioned by user)
db.quiz_attempts.insertOne({
  _id: ObjectId(),
  userId: "user-uuid",
  topicId: "mqtt-protocol",
  score: 50,
  passed: true,
  answers: [
    { questionId: "q1", selectedOption: 0, correct: true },
    { questionId: "q2", selectedOption: 2, correct: false }
  ],
  attemptedAt: ISODate(),
  timeSpentSeconds: 420
});

// User Profiles Collection
db.user_profiles.insertOne({
  _id: "user-uuid",
  email: "user@example.com",
  fullName: "John Doe",
  learningPath: "data-engineer-to-iot",
  preferences: {
    notifications: true,
    difficulty: "intermediate",
    theme: "dark"
  },
  studyGoals: ["build-project", "upskill-work"],
  bookmarkedTopics: ["kafka-basics", "pyflink-intro"],
  createdAt: ISODate(),
  updatedAt: ISODate()
});

// Lab Attempts Collection
db.lab_attempts.insertOne({
  _id: ObjectId(),
  userId: "user-uuid",
  topicId: "mqtt-protocol",
  labId: "lab-mqtt-setup",
  userCode: "version: '3'...",
  testResults: [
    { testName: "syntax valid", passed: true },
    { testName: "service starts", passed: true }
  ],
  hintsUsed: 1,
  solutionViewed: false,
  completedAt: ISODate(),
  timeSpentSeconds: 1200
});
```

### **v1.1+ Schema: Add Neo4j (Knowledge Graph)**

```cypher
// Nodes
CREATE (mqtt:Topic {id: "mqtt-protocol", title: "MQTT", difficulty: 2})
CREATE (wifi:Topic {id: "wifi-basics", title: "WiFi", difficulty: 1})
CREATE (docker:Topic {id: "docker-basics", title: "Docker", difficulty: 2})
CREATE (kafka:Topic {id: "kafka-basics", title: "Kafka", difficulty: 3})

// Prerequisite edges
CREATE (wifi)-[:PREREQUISITE_FOR]->(mqtt)
CREATE (docker)-[:USEFUL_FOR]->(mqtt)

// Reinforcement edges (concept appears again)
CREATE (docker)-[:REINFORCES]->(mqtt)  // Docker mentioned in MQTT labs
CREATE (mqtt)-[:REINFORCES]->(kafka)   // MQTT→Kafka bridge uses MQTT

// User progress nodes (optional, for fast traversal)
CREATE (user:User {id: "user-uuid", xp: 500})
CREATE (user)-[:COMPLETED {score: 50, xp: 50}]->(mqtt)
CREATE (user)-[:COMPLETED {score: 85, xp: 50}]->(wifi)

// Query examples (v1.1+)
// Get all available topics for user
MATCH (user:User {id: "user-uuid"})-[:COMPLETED]->(completed:Topic)
MATCH (available:Topic)
WHERE NOT EXISTS ((available)-[:PREREQUISITE_FOR]->(required:Topic)
                  WHERE NOT (user)-[:COMPLETED]->(required))
RETURN available

// Recommend next topic (shortest path to goal)
MATCH (user:User {id: "user-uuid"})-[:COMPLETED]->(current:Topic)
MATCH path = (current)-[:PREREQUISITE_FOR|USEFUL_FOR*1..3]->(target:Topic)
WHERE NOT (user)-[:COMPLETED]->(target)
RETURN path ORDER BY length(path) LIMIT 5
```

---

## 5. Database Schema (Original—PostgreSQL for v1.0)

```sql
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE topics (
    id                  TEXT PRIMARY KEY,       -- matches frontmatter id
    slug                TEXT UNIQUE NOT NULL,
    title               TEXT NOT NULL,
    category            TEXT NOT NULL,
    difficulty          SMALLINT NOT NULL,
    estimated_minutes   SMALLINT,
    paths               TEXT[] NOT NULL DEFAULT '{}',
    iiot_standard       TEXT,
    content_hash        TEXT NOT NULL           -- SHA of MDX file for seed incremental updates
);

CREATE TABLE topic_prerequisites (
    topic_id        TEXT NOT NULL REFERENCES topics(id),
    prerequisite_id TEXT NOT NULL REFERENCES topics(id),
    PRIMARY KEY (topic_id, prerequisite_id)
);

CREATE TABLE learning_paths (
    id              TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    target_audience TEXT,   -- 'iot-enthusiast' | 'data-engineer' | 'security-specialist'
    entry_topics    TEXT[] NOT NULL DEFAULT '{}'
);

CREATE TABLE user_paths (
    user_id     UUID NOT NULL REFERENCES users(id),
    path_id     TEXT NOT NULL REFERENCES learning_paths(id),
    selected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, path_id)
);

CREATE TABLE user_topic_progress (
    user_id             UUID NOT NULL REFERENCES users(id),
    topic_id            TEXT NOT NULL REFERENCES topics(id),
    status              TEXT NOT NULL DEFAULT 'locked',
    -- locked | available | intro_viewed | flashcards_viewed | quiz_passed | lab_passed | completed
    intro_viewed        BOOLEAN NOT NULL DEFAULT false,
    flashcards_viewed   BOOLEAN NOT NULL DEFAULT false,
    quiz_attempted      BOOLEAN NOT NULL DEFAULT false,
    quiz_passed         BOOLEAN NOT NULL DEFAULT false,
    quiz_score          SMALLINT,
    lab_attempted       BOOLEAN NOT NULL DEFAULT false,
    lab_passed          BOOLEAN NOT NULL DEFAULT false,
    completed_at        TIMESTAMPTZ,
    xp_earned           SMALLINT NOT NULL DEFAULT 0,  -- XP from this topic
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, topic_id)
);

CREATE TABLE user_gamification (
    user_id             UUID PRIMARY KEY REFERENCES users(id),
    total_xp            INTEGER NOT NULL DEFAULT 0,
    current_level       SMALLINT NOT NULL DEFAULT 1,  -- 1-5
    current_streak      SMALLINT NOT NULL DEFAULT 0,  -- consecutive days
    longest_streak      SMALLINT NOT NULL DEFAULT 0,
    last_activity_date  DATE NOT NULL DEFAULT CURRENT_DATE,
    topics_completed    SMALLINT NOT NULL DEFAULT 0,
    labs_completed      SMALLINT NOT NULL DEFAULT 0,
    badges              TEXT[] NOT NULL DEFAULT '{}',  -- array of badge IDs
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE user_badges (
    user_id             UUID NOT NULL REFERENCES users(id),
    badge_id            TEXT NOT NULL,  -- 'linux-fundamentals', 'security-aware', etc.
    earned_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, badge_id)
);

-- Email & Re-engagement Preferences
CREATE TABLE user_email_preferences (
    user_id             UUID PRIMARY KEY REFERENCES users(id),
    email               TEXT NOT NULL,
    subscribed_to_emails BOOLEAN NOT NULL DEFAULT true,
    dormancy_alerts     BOOLEAN NOT NULL DEFAULT true,
    weekly_digest       BOOLEAN NOT NULL DEFAULT true,
    achievement_alerts  BOOLEAN NOT NULL DEFAULT true,
    new_content_alerts  BOOLEAN NOT NULL DEFAULT true,
    last_email_sent_at  TIMESTAMPTZ,
    last_email_opened_at TIMESTAMPTZ,
    unsubscribed_at     TIMESTAMPTZ,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Email Campaign Tracking
CREATE TABLE email_campaigns (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id),
    campaign_type       TEXT NOT NULL,  -- 'dormancy', 'achievement', 'spaced-rep', 'weekly', 'new-content'
    topic_id            TEXT,
    subject             TEXT NOT NULL,
    sent_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    opened_at           TIMESTAMPTZ,
    clicked_at          TIMESTAMPTZ,
    click_count         INTEGER NOT NULL DEFAULT 0
);

-- Recommendation Tracking (for analytics)
CREATE TABLE recommendations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id),
    recommended_topic   TEXT NOT NULL,
    recommendation_type TEXT NOT NULL,  -- 'collaborative', 'content-based', 'behavioral'
    confidence_score    FLOAT NOT NULL,  -- 0.0 to 1.0
    shown_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    clicked_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ
);

CREATE TABLE quiz_attempts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    topic_id        TEXT NOT NULL REFERENCES topics(id),
    score           SMALLINT NOT NULL,
    passed          BOOLEAN NOT NULL,
    answers         JSONB NOT NULL,  -- [{question_id, selected_option_index, correct}]
    attempted_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_utp_user ON user_topic_progress(user_id);
CREATE INDEX idx_qa_user_topic ON quiz_attempts(user_id, topic_id);
CREATE INDEX idx_tp_prereq ON topic_prerequisites(prerequisite_id);
```

---

## 5. API Design (Rust/Axum)

```
GET  /health

# Auth
POST /auth/register                  # Email + password
POST /auth/login                     # Email + password
POST /auth/google                    # Keycloak (open source OAuth2) callback
POST /auth/logout
GET  /auth/me

# Graph
GET  /graph/user              # Full graph annotated with user progress + dagre coordinates
GET  /graph/public            # Unauthenticated preview (all nodes, no progress)

# Topics
GET  /topics                  # List (filterable: path, category, difficulty, iiot_standard)
GET  /topics/:id              # Topic metadata + flashcards
GET  /topics/:id/quiz         # Quiz questions (no correct flags sent to client)
POST /progress/:id/intro      # Mark intro viewed
POST /progress/:id/flashcards # Mark flashcards viewed
POST /progress/:id/quiz       # Submit answers → returns scored result + explanations + newly_unlocked

# Paths
GET  /paths
POST /paths/:id/select        # Inserts synthetic quiz_passed rows for assumed-known topics
GET  /paths/:id/topics        # Ordered topic list

# User
GET  /user/stats
GET  /user/certificates     # List all downloadable certificates
GET  /user/certificates/:pathId/download  # Download PDF certificate

# Certificates (Auto-generated, no approval workflow)
GET  /certificates/:id/verify  # Verify certificate authenticity (QR code endpoint)

# Recommendations (Personalization Engine)
GET  /recommendations/next-topic              # Smart topic suggestion for user
GET  /recommendations/search?query=kafka       # Search with smart suggestions
GET  /recommendations/similar-learners/:topicId  # What users like them did next
GET  /recommendations/feed                    # Personalized homepage feed
POST /recommendations/feedback                # User feedback on recommendations

# User Behavior Tracking (implicit tracking)
POST /analytics/topic-viewed                  # Ping when viewing topic
POST /analytics/search                        # Track search queries
POST /analytics/quiz-attempt                  # Track quiz performance
POST /analytics/lab-attempt                   # Track lab performance

# Email Management
GET  /user/email-preferences                  # User's email settings
POST /user/email-preferences                  # Update email prefs (opt-in/out)
POST /user/email/unsubscribe/:campaignId      # Unsubscribe from campaign
GET  /user/emails                             # Email history
```

### Quiz submission response (key design)

```json
{
  "score": 75,
  "passed": true,
  "results": [
    {
      "question_id": "kbq1",
      "correct": true,
      "selected_option": 1,
      "correct_option": 1,
      "explanation": "Kafka retains records for a configurable duration..."
    }
  ],
  "newly_unlocked": ["kafka-topics-partitions", "mqtt-kafka-bridge"]
}
```

`newly_unlocked` triggers the unlock animation on the map. Computed server-side by re-evaluating the DAG after marking progress.

### Rust crates
`axum`, `sqlx`, `serde`/`serde_json`, `jsonwebtoken`, `argon2`, `petgraph` (DAG traversal + cycle detection), `sha2`, `tower-http`, `tracing`

---

## 6. Frontend Pages and Routing

```
/                              → Landing + path selection preview
/sign-up                       → Registration + onboarding wizard (path selection)
/sign-in                       → Login
/dashboard                     → Stats + recently active + continue prompt
/map                           → Full knowledge graph (React Flow + dagre)
/map?path=data-engineer-to-iot → Graph filtered to path
/topics/[slug]                 → Topic intro (MDX rendered)
/topics/[slug]/flashcards      → Flashcard deck (flip animation)
/topics/[slug]/quiz            → Quiz (answer → explanation → next)
/topics/[slug]/complete        → Completion + unlock animation + next topic suggestions
/paths                         → Browse paths
/settings                      → Account + path management
/certificates                  → View & download all earned certificates
/certificates/:pathId          → Certificate detail + download PDF + share options
```

---

## 6b. Certificates (Free, Downloadable)

### Certificate Types & Completion Requirements
1. **Category Certificates** (e.g., "Linux Fundamentals", "Networking Protocols")
   - Trigger: Complete all topics in a category
   - Design: Professional PDF with learner name, category, date, XP earned, topics covered
   - Shareable: Download PDF, share on LinkedIn (badge), embed in portfolio

2. **Path Completion Certificates** (e.g., "Full Stack IoT Engineer")
   - Trigger: Complete selected learning path (all topics across categories)
   - Design: Premium design (holographic-style border, seal, multi-language support)
   - Includes: XP total, paths completed, estimated hours, date range (start→completion)
   - Verification: QR code links to `/certificates/:id/verify` showing issuer info + date

3. **Challenge Certificates** (v1.1+, optional)
   - Trigger: Complete weekly/monthly challenges
   - Design: Smaller badge-style certificate

### Certificate Generation Flow
1. User completes final topic in path/category
2. Backend auto-generates PDF (no approval needed)
3. Certificate stored as MongoDB document:
   ```javascript
   db.certificates.insertOne({
     _id: ObjectId(),
     userId: "user-uuid",
     type: "path",  // 'path' | 'category' | 'challenge'
     pathId: "iot-to-cloud",
     issuedAt: ISODate(),
     verificationCode: "uuid",  // QR code links to this
     xpEarned: 2500,
     topicsCompleted: 91,
     estimatedHours: 128
   })
   ```
4. User sees notification: "🎓 Path Complete! Download your certificate"
5. PDF downloadable from `/certificates/:pathId/download`
6. Share button: LinkedIn, Twitter, email

### Technical Implementation
- **PDF Generation**: `pdfkit` (Rust crate) or `wkhtmltopdf`
- **Template**: Certificate HTML template + learner data injected
- **Verification**: `/certificates/:verificationCode/verify` returns issuer info + issue date
- **Storage**: PDF stored in S3 / Cloudflare R2 (free tier), link in certificate DB
- **No blockchain initially** (v1.0); simple SHA256 verification code sufficient

### Key components

- `KnowledgeMap.tsx` — React Flow canvas, custom TopicNode, PathFilter chips, unlock animation
- `FlashcardDeck.tsx` + `FlashcardCard.tsx` — Framer Motion rotateY flip
- `QuizRunner.tsx` — State machine: `answering → submitted → results`
- `OptionButton.tsx` — Idle / selected / correct / incorrect visual states
- `ExplanationPanel.tsx` — Slides up after answer, shows teaching explanation for selected option
- `QuizResults.tsx` — Per-question review accordion, score, "Review all" toggle

### State management
- **Server state**: TanStack Query (all API calls, optimistic updates on progress mutations)
- **Client state**: Zustand (mid-quiz selections, flashcard index, graph filter state)
- **Auth**: React Context from `/auth/me`

---

## 7. Quiz & Lab Teaching Mechanism (Learning-First, Not Exam-First)

**Philosophy**: This is a learning platform, not an exam platform. Users should never get stuck. Hints and solutions are freely available.

### Quiz Flow (Teaching-Focused)
1. User selects option → question locks (no changing)
2. Selected option turns green/red immediately; all options reveal colors
3. `ExplanationPanel` slides up showing explanation for **the selected option** (correct options reinforce reasoning; wrong options correct the specific misconception)
4. "See full explanation" link provides expanded context
5. "Show answer" button available immediately (not gatekeeping knowledge)
6. "Next question" button appears — users can proceed even if they didn't get it right
7. After all questions: full review with score + per-question accordion + "revisit this topic" suggestion (if score < 60%)

**Key**: No gating. Low score doesn't block progression. Focus is learning, not assessment.

### Hands-On Lab Flow (Guided Learning)
1. User reads **Problem Statement** (left pane)
2. Template code provided (fill-in-the-blanks or partial skeleton)
3. User writes code in **Coding Area** (right pane, with Monaco Editor autocomplete)
4. Tests run automatically as they type (live feedback)
5. **Hints available at any time** (tiered: conceptual hint → specific hint → code snippet)
6. **Solution available immediately** (toggleable, not hidden behind conditions)
7. User can copy solution and move forward (no judgment, goal is learning)
8. "Compare with solution" shows diff between user's code and reference solution (educational, not grading)
9. "Next lab" button appears after first test passes OR after 3 attempts + 2 hint views

**Key Difference**: Traditional platforms (LeetCode, HackerRank) gate progression on perfect solutions. LearnDataFlow says: "See the answer, understand why, move forward." Learning > Assessment.

### Progression Model
- **Quiz score < 60%?** Suggestion: "This topic is tricky. Review the flashcards again, then retake the quiz."
- **Lab not working?** Immediate suggestion: "Stuck? Here's the solution and an explanation of each line."
- **User skips labs?** Allowed. They can come back later (marked as "not attempted" in progress).

This removes friction and shame from learning technical subjects where mistakes are expected.

---

## 8. Auth & Onboarding

### Auth Flow
1. **Email/Password** (traditional)
   - Register: email + password + verify via link
   - Login: email + password + MFA (TOTP) optional but encouraged
2. **Keycloak (open source OAuth2)** (social login, frictionless)
   - "Sign in with Google" button on login page
   - First-time users: auto-create account + go to path selection wizard
   - Existing users: auto-login
   - No password required for Google SSO users (MFA via Google Account)

### Onboarding After Auth

**Path Selection Wizard** (3 screens):
1. "Who are you?" 
   - IoT/Hardware Enthusiast
   - Data Engineer / Cloud Developer
   - Security Specialist
   
2. "What's your goal?"
   - Understand full stack (IoT → cloud → data pipeline)
   - Build a project
   - Upskill for work
   - Explore new skills
   
3. "Your starting map"
   - Show mini knowledge graph with first 5-6 topics unlocked for selected path
   - "Start learning" button begins Linux fundamentals block

---

## 9. Path Selection UX (Learning Paths)

3-screen flow at registration:
1. "Who are you?" — IoT/Hardware Enthusiast | Data Engineer/Cloud Dev | Security Specialist
2. "What's your goal?" — checklist (build a project / understand full stack / upskill for work / explore)
3. "Your starting map" — mini graph showing first 5-6 unlocked topics

`POST /paths/:id/select` inserts synthetic `quiz_passed` completions for topics the path assumes known:
- **Data Engineer path**: pre-completes `docker-basics`, `kafka-basics`, `what-is-microcontroller`
- **IoT Enthusiast path**: pre-completes `what-is-microcontroller`, `arduino-basics`, `gpio-fundamentals`
- **Security Specialist path**: pre-completes `wifi-basics`, `docker-basics`, `ssh-basics`

---

## 9. Library Recommendations

### Frontend (React/Next.js)
| Concern | Library | Rationale |
|---|---|---|
| Graph visualization | Cytoscape.js | Better for 90+ node graphs; desktop-first |
| Graph layout (server-side) | `dagre` / `@dagrejs/dagre` | Deterministic DAG layout |
| Animations | `framer-motion` | Flashcard flip, unlock animations |
| UI components | `shadcn/ui` (Radix + Tailwind) | Owned, accessible, no vendor lock-in |
| Forms | `react-hook-form` + `zod` | Validation on auth + lab configs |
| Data fetching | `@tanstack/react-query` | Caching, optimistic updates |
| Client state | `zustand` | Mid-quiz selections, lab state |
| MDX rendering | `next-mdx-remote` | Intro pages |
| Icons | `lucide-react` | Consistent, tree-shakeable |
| **Code editor** | **Monaco Editor** (via `@monaco-editor/react`) | IntelliSense, syntax highlighting, familiar VS Code UX |
| **Terminal emulator** | **Xterm.js** | Browser-based terminal, supports WebSocket for real-time output |
| **Diff viewer** | **react-diff-viewer** | Show expected vs actual output in labs |
| **Ad network** | **Ethical Ads (open source friendly ad network)** | Non-intrusive ads for monetization (sidebar, banner placements) |

### Backend (Rust)
See §5 crates, add:
- `tokio` — async runtime for concurrent lab executions
- `docker` (via `bollard`) — spawn sandboxed containers for labs
- `websocket` (via `tokio-tungstenite`) — real-time terminal output to frontend
- `jsonschema` — validate lab YAML schema
- `printpdf` / `pdfkit` — PDF certificate generation
- `mongodb` — MongoDB driver for content + quiz attempts + behavior tracking
- `neo4j` (v1.1+) — Neo4j graph queries (optional for MVP)
- `lettre` — Email sending (SMTP client)
- `serde` — Serialization for recommendation payloads
- `rand` — Random sampling for collaborative filtering
- `ndarray` / `linfa` — Linear algebra for recommendation engine (if needed for ML)
- `llama-cpp-rs` or `candle` — Local LLM inference (Nemotron, Llama, Code Llama)
- `regex` — Pattern matching for rule-based hint system
- `tokenizers` — Tokenization for LLM models (open source)
- GPU support: CUDA, ROCm, Metal (depending on infrastructure)

### Lab Sandboxing
- **Docker** — container isolation, resource limits (CPU/memory/network)
- **Firecracker** (optional, v1.1+) — lightweight microVMs for stronger isolation if needed
- **Kubernetes** (v1.2+) — auto-scale lab environments for high volume

---

## 10. Real-World Lifecycle Realities (Informed by Canvas, Moodle, Open edX)

**From 2026 Canvas breach (275M records, 9K schools) and Moodle/Open edX deployments:**

### Security by Design (Not Afterthought)
1. **Identity & Access Control**
   - Implement MFA from day 1 (TOTP required for free accounts; OAuth optional)
   - Session-token telemetry (detect credential abuse early)
   - Audit logging of all admin actions (FERPA requirement)
   - Encryption in-transit (TLS) and at-rest (database)

2. **Dependency Management**
   - Automated scanning (Dependabot, Snyk) in CI/CD
   - Version pinning strategy: major.minor.patch semantic versioning
   - Deprecation window: warn users 6 months before breaking changes
   - Security patches = hot fixes; feature releases = quarterly

### Deployment Realism (Not Just SaaS)
1. **Production-Ready Artifacts**
   - Docker Compose for local dev (single `docker-compose up`)
   - Helm charts + Kubernetes operator for institutional self-hosting (Moodle Operator pattern)
   - Pre-flight checklist: firewall rules, LTI OIDC URLs, TLS certificate setup
   - Common gotchas documented: trailing slashes in URLs, JWT claim mismatches, proxy timeouts

2. **LTI 1.3 Compliance** (not LTI 1.0)
   - OAuth2 token validation, not just URLs
   - Explicit `deployment_id` claims required (2024 spec)
   - Grade passback + content item selection
   - Clear error messages for OIDC failures ("Missing required claim: 'lti_user_id'")

### Performance From Day 1
1. **Database Strategy**
   - Indexes on `users.email`, `user_progress.user_id`, `user_progress.topic_id` at install
   - Connection pooling (PgBouncer) for high-concurrency deployments
   - Read replicas for analytics queries (don't starve application queries)

2. **Caching Layer**
   - Redis for sessions (share across web server instances)
   - In-memory cache (Rust level) for topic graph (invalidate on content update)
   - CDN for static flashcard decks (JSON + images)

3. **Query Optimization**
   - Avoid `SELECT *` on large tables
   - Batch user progress updates (don't hit DB for each question answered)
   - Pre-compute graph availability (cached per user, invalidated on quiz completion)

### Maintenance (60-80% of Lifecycle Cost)
- **Realistic estimate**: For every hour shipping features, plan 5-8 hours maintaining production
- **Timeline**: v1.0 ships in 12 weeks, then expect 2-3 engineers on maintenance/support by month 4
- **Vendor risk**: Rust/NAPI/PostgreSQL are stable; React/Next.js update quarterly
- **Incident response**: 24-hour patch SLA for security issues, 72-hour for critical bugs

### Developer Experience Drives Adoption (Not Features)
Research shows: **users complain 3x more about documentation/error messages than missing features.**
- Clear setup errors: "Error: Missing POSTGRES_PASSWORD env var. Set it with: `export POSTGRES_PASSWORD=...`"
- Step-by-step LTI integration guide with example requests/responses
- Video walkthrough of Kubernetes operator setup
- Troubleshooting guide for 10 most common issues (covers 80% of support tickets)

---

## 9b. AI-Powered Adaptive Help System

### **Goal: AI as a Smart Tutor**

Analyze how users approach problems and provide personalized hints, clues, and explanations in real-time.

### **AI Help Triggers**

**1. Quiz Help** (user struggling on questions)
- **On wrong answer**: AI analyzes the misconception
  - User selects wrong option → AI generates personalized explanation
  - "I see you think [misconception]. Actually, [explanation]. Here's an analogy: [analogy]"
  - Example: User picks "replication factor" for Kafka retention → AI explains "Replication protects broker failure, not rate mismatch"
  
- **"Explain this more"** button: AI generates deeper explanation
  - Uses Claude API or open source LLM to generate context-specific explanation
  - Includes real-world analogies, code examples if relevant

**2. Lab Help** (user stuck on coding)
- **"Hint"** button (tiered):
  - Hint 1 (conceptual): "You need to set up 3 services in Docker Compose: [service names]"
  - Hint 2 (specific): "Check the YAML indentation. Port mapping should be `8080:1883`"
  - Hint 3 (code snippet): Show partial solution with `____` placeholders
  
- **"Why is this failing?"** button: AI analyzes error message
  - User gets error: `address already in use`
  - AI explains: "Port 1883 is already in use. You have two options: [option 1], [option 2]"
  - Suggests: "Try changing the port to 1884"

- **"Explain my code"** button: AI reviews submitted code
  - User submits lab solution
  - AI reads code and explains what it does
  - Suggests improvements: "Your code works! FYI, you could simplify this with [suggestion]"

**3. Topic Questions** (user confused about concept)
- **"Ask AI about this topic"** chatbot (on topic page)
  - User: "What's the difference between MQTT QoS 0 and QoS 1?"
  - AI: "QoS 0 = fire-and-forget (at most once). QoS 1 = guaranteed delivery (at least once). Here's when to use each: [explanation]"
  - Context-aware: AI knows which topic they're reading, personalizes explanation

**4. Search Help**
- **Smart search autocomplete**: "Search for 'kafka security'" → AI suggests related topics
- **Clarifying questions**: "Are you looking for Kafka SASL auth, TLS config, or ACLs?"

### **AI Models (100% Open Source)**

**Architecture: Layered approach (no proprietary APIs)**

```
User Request
    ↓
Is this a common pattern? → YES → Rule-based hint (instant, no cost)
    ↓ NO
Use self-hosted open source LLM (low cost, high speed)
```

**Recommended: Self-Hosted Open Source LLMs**

**Option 1: Nemotron (NVIDIA)** - Fast inference, efficient
- **Nemotron 3.1 8B** or **70B** (open source)
- Optimized for low latency and efficiency
- Cost: Minimal (self-hosted)
- Quality: Good for hints, explanations, code review
- Speed: Very fast inference (good for real-time help)

**Option 2: Llama 3** (Meta) - High quality, open source
- **Llama 3 8B** or **70B** (open source)
- Excellent for explanations and code analysis
- Cost: Minimal (self-hosted)
- Quality: Strong for educational content
- Speed: Good inference speed

**Option 3: Code Llama** (Meta) - Specialized for code
- **Code Llama 7B/13B/34B** (open source)
- Best for: Lab help, code review, debugging
- Cost: Minimal (self-hosted)
- Quality: Excellent for code-related questions
- Speed: Good for real-time help

**Hybrid Approach (Recommended for v1.0)**:
1. **Rule-based**: Common errors, patterns (instant, no cost)
2. **Nemotron 3.1 8B**: Fast hints, explanations (self-hosted)
3. **Code Llama 13B**: Specialized code help (self-hosted)
4. Scale up to 70B models if needed (GPU permitting)

**Why Open Source Only**:
✅ No API costs (self-hosted inference)  
✅ No vendor lock-in (use any LLM model)  
✅ Data privacy (all processing stays on platform)  
✅ Full control (can fine-tune on your data)  
✅ No rate limits (unlimited inference)

### **Example: Lab Help Flow**

**User trying Docker Compose lab, stuck:**

```
User: "My docker-compose up keeps failing"

System checks:
  1. Is this a common error? (rule-based lookup)
     → YES: "Port already in use" (matches pattern)
     → Instant help: "Try `lsof -i :1883` to find what's using the port"
  
  2. User still stuck, clicks "Explain my errors"
     → Send error logs to self-hosted LLM
     → LLM analyzes: "Your service depends_on redis, but redis isn't starting"
     → Response: "Check: (1) Is redis image correct? (2) Are environment variables set? (3) Is network config right?"
  
  3. User still stuck, clicks "Premium AI Review"
     → Send code + errors to Claude API
     → Claude: "Your issue is [root cause]. Here's the fixed YAML: [code]"
     → Also: "Pro tip: You could improve [optimization]"
```

### **AI Knowledge Base** (rule-based fallback)

For common problems, use deterministic rules (no LLM needed):

```javascript
const hintPatterns = [
  {
    error: "address already in use",
    hints: [
      "Port is already in use by another service",
      "Try changing the port number or killing the other process",
      "Use `lsof -i :PORT` to find what's using it"
    ]
  },
  {
    error: "connection refused",
    hints: [
      "Service isn't running or listening on that port",
      "Check service is started: `docker ps`",
      "Check the port mapping in docker-compose.yml"
    ]
  },
  {
    misconception: "MQTT QoS",
    hints: [
      "QoS 0 = at most once (no guarantee)",
      "QoS 1 = at least once (guaranteed, may duplicate)",
      "QoS 2 = exactly once (most reliable, slowest)"
    ]
  }
];
```

### **Comprehensive Tracking for AI (Open Source LLM)**

✅ **Track AI interactions**: Every hint requested, error analysis, code review (100% on-platform)  
✅ **Analyze patterns**: Which help types work best, optimize hint quality  
✅ **User data**: All stays local, no third-party API calls, fully tracked for analytics  
✅ **AI feedback loop**: "Users who use this hint improve by X%" → fine-tune models over time  
✅ **Accuracy**: Mark responses as "AI generated" (not authoritative)  
✅ **Open source inference**: Nemotron/Llama/Code Llama running locally (no API costs)  

### **Backend Integration**

Add to Rust backend:
- `llm` crate for local model inference (Llama 2 / Code Llama)
- `reqwest` for Claude API calls (if enabled)
- Redis cache for hint responses (same error → same hint, no re-compute)

**Endpoints**:
```
POST /ai/hint                    # Generate hint for lab
POST /ai/explain-error           # Analyze error message
POST /ai/explain-topic           # Explain concept
POST /ai/review-code             # Code review + feedback
POST /ai/question                # Answer user question
GET  /ai/search-suggestions      # Smart search autocomplete
```

---

## 10a. Confidence-First Onboarding (Make Users Feel Intelligent)

### **Psychology: Early Wins Build Motivation**

**Principle**: Every user's first 3 topics are intentionally EASY. Make them feel smart. Build confidence. Then gradually increase difficulty.

**First 3 Topics** (always difficulty 1.0, designed for victory):
1. **"Welcome to LearnDataFlow"** (5 min)
   - Plain English: "What is IoT?" (no jargon yet)
   - 3 flashcards (definitions only)
   - 3 quiz questions (80%+ should pass)
   - No lab (just an intro)
   - Celebration: "🎉 You completed your first topic! You're already learning!"

2. **"Linux Terminal Basics"** (20 min)
   - `ls`, `cd`, `pwd` (3 commands)
   - 5 flashcards
   - 5 quiz questions (easy, confidence-building)
   - Terminal lab (auto-complete, hints, pre-typed commands visible)
   - Celebration: "⭐ Terminal wizard unlocked! You're a natural!"

3. **"What is Docker?"** (20 min)
   - Analogy: "Containers are like shipping boxes for code"
   - 5 flashcards
   - 5 quiz questions
   - Docker Compose lab (they just press "run", it works)
   - Celebration: "🚀 Developer mode unlocked! You deployed code!"

**After First 3 Easy Topics**:
- User has: 150+ XP, 3 badges, 3-day streak
- Psychology: "I've learned Linux AND Docker! I'm smart!"
- Recommendation engine now suggests difficulty 1.5-2.0 topics

**Difficulty Progression** (no jumps):
```
1.0 → 1.0 → 1.0 → 1.5 → 1.5 → 2.0 → 2.0 → 2.5 → 3.0 → 3.5 → 4.0
(easy) ..................... (moderate) .................. (hard)
```

Never jump 1.0 → 3.0 (that's where people quit)

**Positive Reinforcement Language**:
- ✅ "You're on fire! 🔥" (instead of "You passed")
- ✅ "You mastered this!" (instead of "You got 75%")
- ✅ "Great debugging!" (instead of "You found the error")
- ❌ Never: "You failed" → say "Let's try again"
- ❌ Never: "Only 60%" → say "6/10 — close! One more attempt?"

**Victory Celebrations**:
- Topic complete: Confetti + badge + XP popup
- First lab: "You're a developer now! 🎉"
- 3-day streak: "You're consistent! Keep it up!"
- First certificate: "Share this on LinkedIn! You earned it!"
- 10 topics: "You've learned more than 80% of beginners. You're top tier!"

**Confidence Tracking** (per user):
```
confidence_score = (
  topics_completed * 10 +
  current_streak * 5 +
  badges_earned * 15 +
  avg_quiz_score * 0.5
) / 100  // 0-100 scale
```

- confidence < 30: Only difficulty 1.0 topics
- confidence 30-60: Mix of 1.0-1.5 topics
- confidence 60-80: Mix of 1.5-2.5 topics
- confidence > 80: Can handle 3.0+ difficulty

---

## 10b. Recommendation Engine & Engagement System

### **Goal: Keep Users Hooked & Coming Back**

**Comprehensive Behavior Tracking** (all user interactions tracked):
- **Topic interactions**: View duration, scroll depth, section re-visits, intro vs. lab focus
- **Quiz performance**: Every answer (right/wrong), time per question, hint usage, retakes, score progression
- **Lab interactions**: Code submitted (every keystroke can be tracked), errors, debugging approach, hint tier reached, solution views
- **Search behavior**: Every query typed, order of results clicked, topics discovered via search
- **Session patterns**: Time of day, device, browser, session duration, time between sessions
- **Engagement signals**: Email opens, email clicks, recommendation interactions, badge views, profile views
- **Learning patterns**: Struggle points (where they get stuck), learning pace, difficulty preferences
- **Error patterns**: Common mistakes, which concepts confuse them, error recovery approach
- **Social interactions**: If community enabled - who they follow, message patterns, peer influence

**Data stored in MongoDB**:
```javascript
db.user_behavior.insertOne({
  userId: "user-uuid",
  timestamp: ISODate(),
  event: "topic_viewed" | "quiz_attempted" | "lab_attempted" | "search_performed",
  topicId: "mqtt-protocol",
  duration_seconds: 1200,
  quiz_score: 75,
  search_query: "kafka security",
  metadata: { /* event-specific data */ }
});
```

### **Recommendation Engine (Hybrid Approach)**

**1. Collaborative Filtering**
- "Users who completed [Topic A] often struggle with [Topic B]" → recommend [Topic B] with extra hints
- "Users who completed [Topic A] → [Topic B] → [Topic C]" (learning path patterns)
- Recommend topics based on similar learners' paths

**2. Content-Based Filtering**
- User completes "MQTT Basics" → recommend "MQTT v5 Features" (same category, next difficulty)
- User searches "Kafka" → recommend related topics (security, producers/consumers)
- User excels at Docker → recommend Kubernetes (related skill progression)

**3. Behavioral Signals**
- High engagement (completes topics quickly) → recommend harder topics (challenge them)
- Low engagement (takes forever on topics) → recommend easier topics (rebuild confidence)
- Dormant >7 days → email: "You were learning [Topic]. Ready to continue?"
- Quiz score <60% → recommend: "Review [Topic] with spaced repetition before next"

### **Recommendation API Endpoints**

```
GET /recommendations/next-topic
  → Returns: { topicId, reason, confidence_score }
  Example: "Based on your MQTT learning, try MQTT v5 Features next"

GET /recommendations/search-suggestions?query=kafka
  → Auto-complete search with smart suggestions
  Example: ["kafka-basics", "kafka-security", "kafka-streams"]

GET /recommendations/similar-learners?topicId=mqtt
  → Show what similar users did next
  Example: "80% of learners who completed MQTT went to Kafka"

GET /recommendations/personalized-feed
  → Home page feed of recommended topics
  → Ranked by: relevance, difficulty_match, community_popularity
```

### **Email Re-engagement System**

**Email Triggers**:
1. **Dormancy Alert** (after 7+ days inactive)
   - Subject: "Your learning streak is paused 🔥 Come back?"
   - Body: "You were learning [Topic]. Pick up where you left off!"
   - Include: direct link to topic, progress reminder, new topics added

2. **Achievement Unlocked**
   - Subject: "🏆 You unlocked [Badge]!"
   - Body: Show badge, suggest next challenge
   - Timing: immediate on unlock

3. **Spaced Repetition Reminder**
   - Subject: "Time to review [Topic]?"
   - Body: "You learned this X days ago. Here's a quick flashcard reminder"
   - Timing: algorithmic (Ebbinghaus curve)

4. **Weekly Digest** (opt-in)
   - Subject: "Your learning week in review"
   - Body: Stats (XP, topics, streak), new topics added, friend activity
   - Timing: Sunday evening

5. **Challenge Invitation** (peer gamification)
   - Subject: "[Friend] is on a 14-day streak! Can you catch up?"
   - Body: Show friend's progress, suggest competition topics
   - Timing: when friend surpasses user

6. **New Content Alert**
   - Subject: "New topics in [Category] you love! 🎓"
   - Body: "3 new Kafka topics just dropped. Check them out!"
   - Timing: on content publish

**Email Service** (open source):
- **SendGrid alternative**: Postal (self-hosted open source email server)
- **Or**: Mailgun for transactional email
- **Template engine**: Handlebars (inject user data into templates)
- **Tracking**: Link clicks, open rates (understand what re-engages users)

### **Personalization Rules**

**Dynamic Topic Ordering** (per-user):
- User 1 (fast learner): Show harder topics next, suggest challenges
- User 2 (slow learner): Show gentler progression, build confidence
- User 3 (searcher): Highlight search-discovered topics they haven't completed
- User 4 (gamer): Highlight streak, badges, leaderboards

**Knowledge Graph Customization**:
- Show next-likely-topics at top of each topic (based on similar users)
- Highlight "trending" topics (most learners doing this path right now)
- Suggest "avoid-if-unprepared" topics (high difficulty spike warning)

**Homepage Feed** (like LinkedIn/Twitter):
- Curated topics based on user interests
- Topics they searched for but haven't completed
- Community highlights ("trending this week")
- Friend activity (if enabled)

### **Analytics Dashboard** (for admins/creators)

Track platform engagement:
- Retention cohort analysis (% of users active after 1 week, 1 month, 3 months)
- Recommend performance (CTR, conversion rate of recommendations)
- Email engagement (open rate, click rate per trigger type)
- Topic engagement (avg time, completion rate, search frequency)
- Funnel analysis (registration → first topic → first lab → first cert)

---

## 10c. MVP Approach: Build Platform First, Strong Foundations Second

**Why Content Comes After v1.0:**
- Platform is the foundation; topics can be added anytime
- v1.0 launches with 5-8 **sample topics** demonstrating the pattern
- Full syllabus (91+ topics on foundations) authored incrementally in v1.1+
- Advanced topics (OpenCV, Edge AI) come later after foundations are solid

**MVP v1.0 Topics** (Linux Fundamentals Only):
These 8 topics prove the platform works and build unbreakable foundation for everything that follows.

1. **"Welcome to LearnDataFlow"** (5 min, difficulty 1.0)
   - What is Linux? (plain English, no jargon)
   - 3 flashcards
   - 3 quiz questions (easy wins)

2. **"Linux Terminal Basics"** (20 min, difficulty 1.0)
   - `ls`, `cd`, `pwd`, `mkdir` commands
   - 5 flashcards
   - 5 quiz questions
   - Interactive terminal lab

3. **"File Permissions"** (20 min, difficulty 1.0)
   - `chmod`, `chown`, file ownership
   - 5 flashcards
   - 5 quiz questions
   - Lab: Change permissions, understand results

4. **"Processes and Services"** (20 min, difficulty 1.5)
   - `ps`, `top`, `systemctl`, background processes
   - 5 flashcards
   - 5 quiz questions
   - Lab: Start/stop services, monitor processes

5. **"Package Management"** (20 min, difficulty 1.0)
   - `apt`, `yum`, installing/removing packages
   - 5 flashcards
   - 5 quiz questions
   - Lab: Install software, manage packages

6. **"Networking Commands"** (25 min, difficulty 1.5)
   - `ping`, `ip addr`, `ss`, `netstat`, `curl`
   - 6 flashcards
   - 6 quiz questions
   - Lab: Check IP, test connectivity, view open ports

7. **"Text Tools"** (20 min, difficulty 1.5)
   - `grep`, `awk`, `sed`, `cat`, `less`, `tail -f`
   - 6 flashcards
   - 6 quiz questions
   - Lab: Filter files, extract data, monitor logs

8. **"Bash Scripting Basics"** (25 min, difficulty 2.0)
   - Writing simple shell scripts
   - Variables, loops, conditionals
   - 6 flashcards
   - 6 quiz questions
   - Lab: Write working bash script

**Foundation Layer Roadmap** (v1.1-v1.2):
- Linux fundamentals (8 topics)
- Networking concepts (8 topics)
- Firewall & security (6 topics)
- Microcontroller basics (6 topics)
- Basic protocols (MQTT, HTTP) (4 topics)
- **Total: ~30 foundation topics**

**Intermediate Layer Roadmap** (v1.3-v2.0):
- Edge computing architecture (5 topics)
- IoT data pipelines (8 topics)
- Edge storage & caching (4 topics)
- Real-time processing (Kafka, PyFlink) (6 topics)

**Advanced Layer Roadmap** (v2.0+):
- **OpenCV fundamentals** (image processing)
  - Prerequisite: Linux, Python, microcontrollers
  - Topics: Image loading, filtering, feature detection, object detection
  
- **Edge AI & ML** (running models on edge)
  - Prerequisite: Python, data pipelines, microcontrollers
  - Topics: TensorFlow Lite, ONNX, model optimization for edge
  
- **Computer Vision on Edge**
  - Prerequisite: OpenCV, Edge AI, microcontrollers
  - Topics: Real-time video processing, resource constraints, optimization
  
- **Advanced Edge Computing**
  - Prerequisite: Edge computing basics, IoT pipelines, security
  - Topics: Federated learning, edge orchestration, multi-device coordination

**This shows**:
✅ Auth + path selection works  
✅ Quiz engine with teaching explanations works  
✅ Lab runner (code editor + terminal) works  
✅ Progress tracking works  
✅ Gamification (XP, badges, unlock animation) works  
✅ Certificates generate correctly  
✅ Knowledge graph traversal works  
✅ Foundation topics are gateway to advanced topics  

**After v1.0 ships**:
1. Content authors build out foundation topics (v1.1-v1.2)
2. Intermediate topics added (v1.3-v2.0)
3. Advanced topics (OpenCV, Edge AI) added based on foundation completion rates

---

## 11. Phased Delivery (Full Lifecycle)

### v1.0 — Core Learning Loop + Production Readiness (14-16 weeks)
**Goal:** Ship with security, operational readiness, hands-on labs, and great DX from day 1.

**Monetization Model**: 
- **Learning**: 100% FREE to all users. Forever. No paywall, no subscription, no premium tiers.
- **Revenue**: Ethical Ads (open source friendly ad network) integration only (non-intrusive ad placements)
  - Sidebar ads (between topics on knowledge graph)
  - In-app banner ads (non-blocking, dismissable)
  - No ads in quiz/lab areas (distraction-free learning during practice)
- **Philosophy**: Learning should never be gatekept. All features free forever, ads-supported.

*Weeks 1-10: Core MVP*
- Auth (register/login/logout + MFA + Keycloak (open source OAuth2))
- **Free, open enrollment** (no subscription, no payment)
- 3 learning paths with onboarding wizard
- **Linux fundamentals block (8 topics)** — mandatory universal entry point
- **20 topics authored** across all 7 categories (representative IIoT concepts)
- Security callout panel in topic UI (`securityFocus` frontmatter flag)
- Intro pages (MDX), flashcard decks, quiz engine with per-option explanations
- Knowledge graph map (Cytoscape.js for 90+ nodes, not React Flow)
- Lock/unlock logic + newly_unlocked animation
- Progress persistence (PostgreSQL + MongoDB)
  - PostgreSQL: users, auth, gamification (XP, streaks, badges)
  - MongoDB: topics, labs, quiz attempts, user preferences
- **Hands-on labs for 50% of topics** (Linux terminal labs + Docker Compose labs)
  - Monaco Editor for code input (syntax highlighting, autocomplete)
  - Xterm.js for terminal output (real-time WebSocket)
  - Auto-grading with test cases
  - Tiered hints + solution reveal (learning-first, no gating)
  - Lab templates (fill-in-the-blanks, partial skeleton)
- **Gamification**: XP system, streaks, badges, levels 1-5, daily challenges
- **Certificates**: Auto-generated PDF certificates for category + path completion
  - Linux Fundamentals Certificate (after 8 Linux topics)
  - Path completion certificates (shareable on LinkedIn)
  - No approval workflow (auto-generated)
- **Recommendation Engine** (keep users engaged):
  - Behavior tracking (topic views, quiz attempts, searches)
  - Next-topic suggestions (collaborative + content-based filtering)
  - Personalized homepage feed (ranked by relevance)
  - Search suggestions (auto-complete based on community patterns)
- **Email Re-engagement System**:
  - Dormancy alerts ("Come back?" after 7+ days)
  - Achievement notifications (badge unlocks)
  - Spaced repetition reminders (flashcard reviews)
  - Weekly digest (stats, new topics, streaks)
  - New content alerts (when topics published)
  - Email preferences (opt-in/out per campaign type)
- **AI-Powered Help System** (adaptive tutor):
  - Personalized hints for labs (tiered: conceptual → specific → code snippet)
  - Error explanation ("Why is this failing?" → AI analyzes error)
  - Code review ("Explain my code" → AI feedback + suggestions)
  - Quiz help ("Explain this more" → AI generates personalized explanation)
  - Topic Q&A (chatbot answers questions about current topic)
  - Smart search suggestions (autocomplete with AI)
  - Hybrid model: Rule-based for common patterns (instant), self-hosted LLM for complex (Llama 2 / Code Llama)
  - Privacy: All inference local (no third-party API calls by default)
  - Optional Claude API for premium help (user opt-in)
- Docker Compose dev environment

*Weeks 9-12: Operational Hardening*
- Security scanning (Dependabot, Snyk in CI/CD)
- Helm charts + Kubernetes operator (Moodle Operator pattern)
- LTI 1.3 compliance (OAuth2, grade passback, content item selection)
- Audit logging (FERPA compliance: all admin actions logged)
- Performance testing (simulate 1k concurrent users)
- Database indexing + query optimization
- Documentation: LTI setup guide, Kubernetes deployment, troubleshooting (covers 10 most common issues)
- `validate-content.ts` CI (cycle detection + schema validation + jargon checking)

*Week 13-14: Community Hardening*
- Error messages reviewed for clarity (not technical jargon)
- First-time setup video walkthrough
- GitHub issues triage + labeling (good-first-issue, documentation)
- Dependency update strategy documented (version pinning, security backport policy)

### v1.1 — Full Curriculum + Institutional Adoption (10-12 weeks after v1.0)
*Timeline: Month 5-6 of lifecycle*

- All 83 topics authored and validated
- IIoT standard tags on topics (IEC 62443, OPC-UA, MQTT v5, etc.)
- User stats dashboard (completion %, streak, time spent, weak topics)
- Graph search (type to highlight nodes)
- Quiz attempt history + performance analytics
- Lateral link suggestions panel
- Certificates / completion badges (institutional credentialing)
- SCORM export option (legacy institutional compatibility)
- Spaced repetition engine (weekly practice recommendations)
- Role-based access (admin, instructor, content-creator)
- Instructor dashboard (monitor cohorts, identify struggling students)

### v1.2 — Platform Scaling + Real-World Edge Cases (10-12 weeks after v1.1)
*Timeline: Month 9-10 of lifecycle*

- Read replicas + analytics database (don't starve application queries)
- Batch progress updates (optimize for quiz submission surge)
- i18n/localization (support non-English locales)
- Windows/Mac dev environment documentation (platform-specific setup)
- Network edge cases: proxy, VPN, firewall timeout troubleshooting
- Maintenance runbooks (on-call procedures, incident response)
- Dependency update automation (quarterly security patch cycle)
- Community plugin system (custom topic types, assessment types)

### v2.0 — Simulation + Advanced Learning (Parallel track, start month 6+)
- Virtual sensor simulator (MQTT message generation in browser)
- Node-RED workflow sandbox (browser-based visual programming)
- Modbus/SCADA simulation (ModSim integration)
- PyFlink/Kafka code sandbox (write streaming aggregations)
- 3D hardware visualization (Three.js)

### v3.0 — Enterprise Features (12+ months)
- SSO / SAML integration (institutional identity)
- Advanced analytics (cohort performance, curriculum effectiveness)
- A/B testing framework (for content optimization)
- Custom curriculum builder (institutions design their own paths)
- API-first mobile app (iOS/Android native)

### Ongoing (Monthly + Quarterly)
- **Monthly**: Security patches, bug fixes, performance monitoring
- **Quarterly**: Feature releases, major dependency updates (with deprecation windows)
- **Community**: Triage issues, respond to questions, accept pull requests

---

## 11. Research-Informed Design Decisions

**From platform design research:**

1. **Spaced Repetition + Active Recall** — Duolingo's model wins over passive content. Implement: (1) lesson-end reviews of mistakes, (2) weekly practice recommendations targeting weak topics. Quizzes must be low-stakes, formative (during learning), not summative (end-of-course).

2. **Knowledge Graph Visualization** — React Flow optimizes for authoring; **Cytoscape.js better for 90+ node prerequisite networks**. Recommendation: Cytoscape for learner-facing visualization (cose-bilkent layout for large graphs), React Flow for curriculum admin editing backend. **Action: Benchmark mobile rendering of both separately.**

3. **IEC 62443 / IIoT Standards** — Don't teach abstract standards. Scaffold with concrete examples: SL1/SL2 first (casual errors → script kiddie attacks). Layer: *why security matters → zones/conduits (diagram) → MQTT TLS (hands-on) → OPC-UA (hands-on)*. Defer SL3-4 to advanced.

4. **Content Authoring at Scale** — Flat MDX fails for 90+ topics. Use: MDX + Git versioning (or headless CMS like TinaCMS). Define modular schema: topic = {overview, key_concepts, real-world_example, hands-on_lab, quiz}. **Store prerequisite graphs separately (YAML) for cross-topic linking.**

5. **Linux Foundation** — Hands-on labs beat theory. Use interactive terminal (KodeKloud model) not videos. Keep to 3-5 hours: file nav, `ls`/`cd`/`mkdir`, permissions, SSH basics, package managers. **Link directly to IoT labs** (e.g., "SSH into a Raspberry Pi").

6. **Security Teaching** — Real-world breach scenarios resonate better than theory. Embed security in every 3rd module (not capstone). 2-3 attack scenarios per level (phishing → firmware tampering → lateral movement). Labs: nmap, SSH hardening, Docker security tied to IEC 62443 SL1.

7. **Flexible Prerequisites** — Duolingo research shows hard gates frustrate; consider *optional bypass tests* (learners can skip prerequisites if they pass a skill assessment). This enables non-linear paths while maintaining rigor.

---

## 12. Critical Architecture Decisions (from Research)

### From LMS & Knowledge Graph Platform Research:

**Decision 1: Graph Visualization Library**
- Initially proposed: React Flow (authoring-friendly)
- **Actual recommendation**: Cytoscape.js for learner-facing views (better for 90+ node graphs)
- Trade-off: React Flow for admin curriculum editor (separate component)
- Implication: Two visualization libraries, but better UX at scale

**Decision 2: Content Storage & Versioning**
- Initially proposed: MDX + Git (works until ~100 topics)
- **Actual recommendation**: PostgreSQL-driven for v1.0, consider Contentful for v1.2
- Rationale: Scales to 500+ courses, built-in versioning, i18n native
- Implication: Database schema + admin editor UI required upfront

**Decision 3: Deployment Strategy**
- **SaaS-first (v1.0)**: Deploy to Vercel (frontend) + Railway/Fly.io (backend)
- **Self-hosting (v1.1+)**: Docker Compose (dev) → Helm charts (Kubernetes)
- Implication: Kubernetes Operator required for enterprise adoption (~4 weeks, month 5)

**Decision 4: Database**
- PostgreSQL (not Neo4j initially)
- Rationale: Operational simplicity, FERPA compliance, upgrade path to Neo4j
- Upgrade trigger: If 50%+ queries involve complex graph traversals

**Decision 5: Platform Strategy**
- **Desktop-only** (laptop/desktop browsers only)
- **Not responsive for mobile**: Knowledge graphs, code editors, terminal emulators need desktop real estate
- **No mobile app, ever**: Topics cannot be meaningfully viewed on phones/tablets
- Implication: Target audience studies on laptops/desktops

**Decision 6: LMS Compliance**
- **v1.0**: MFA required for free accounts, audit logging, FERPA-ready
- **v1.1**: LTI 1.3 (not 1.0), SCORM export, institutional dashboard
- **v1.2**: SSO/SAML, advanced reporting
- Implication: Institutional adoption blocked until v1.1; plan accordingly

### From Real-World Platform Lifecycle Research:

**Security Reality Check**
- Canvas breach (May 2026) proves that SOC 2 ≠ safe. Implement identity-threat detection (session anomalies, impossible travel), not just perimeter controls.
- FERPA compliance requires: encryption in-transit + at-rest, role-based access, immutable audit logs, 30-day user data deletion workflows
- Implication: Security is not a v1.1 feature; bake in from v1.0

**Deployment Complexity Reality Check**
- Institutions fail at LTI setup (URL mismatches, trailing slashes break silent launches)
- Infrastructure failures (database crashing under concurrent load) = 60% of deployment failures
- No standard deployment path = fragmented documentation
- Implication: Kubernetes Operator is mandatory for v1.1 institutional adoption (not optional)

**Performance Reality Check**
- Moodle hits wall at 10K concurrent users (200-500 DB queries per page load)
- Caching (Redis) + read replicas cut load by 60-80%
- Database indexes are make-or-break; missing one index = 1000x slower queries
- Implication: Performance testing at 1K concurrent users required in v1.0 (before shipping)

**Maintenance Reality Check**
- 60-80% of lifecycle cost is maintenance, not development
- Average LMS has 15+ external dependencies; each update risks breaking production
- Estimate: 2-3 engineers on maintenance by month 4
- Implication: Versioning policy + deprecation windows defined in v1.0 docs (not added later)

**DX Reality Check**
- Users complain 3x more about documentation/error messages than missing features
- Bad setup errors = users give up before trying the product
- Implication: Invest in error messages, docs, and troubleshooting guide in v1.0 (not v1.2)

---

## 13. Top Risks & Mitigation

| Risk | Impact | Mitigation | Timeline |
|------|--------|-----------|----------|
| **Content bottleneck** | 83 topics × 5-8 questions × 4 explanations = 1,600+ strings to author. Delays v1.1 launch. | Build quiz engine first with 3-5 topics. Validate UX before scaling. Hire content writers in month 3. | Month 1-3 |
| **Graph visualization at scale** | Cytoscape.js rendering 500 nodes requires desktop resolution. Platform is desktop-only by design. | Design for laptop/desktop (1366px+). No mobile support. Requirement: laptop/desktop browser. | v1.0 design decision |
| **Rust compilation in CI** | Rust backend takes 5-10 min cold; slows CI/CD iteration. | Use `cargo-chef` layer caching + `sccache` remote cache. Split CI: content validation (fast) runs parallel to Rust compile. | Week 1 CI setup |
| **Database query performance** | Missing indexes cause 1000x slowdown under load. Discovered in production = outage. | Benchmark with 1K concurrent users in v1.0. Create indexes at install time. Test queries before deploy. | Week 8-10 (v1.0) |
| **LTI integration friction** | OIDC mismatches, JWT claim bugs = silent failures. Institutions blame your platform. | Comprehensive LTI setup guide + video walkthrough. Pre-built test cases. Clear error messages ("Missing claim: lti_user_id"). | Month 4 (v1.1) |
| **Kubernetes operator complexity** | Moodle Operator took months to stabilize. Building one from scratch = ambitious. | Use existing Helm charts + Kustomize overlays (simpler than custom operator). Add operator in v2.0. | Month 5+ (v1.1) |
| **Security breach or CVE** | Canvas breach (May 2026) = institutional panic, regulatory scrutiny. 0-day in dependency = critical hotfix required. | Security scanning in CI/CD (Dependabot). 24-hour patch SLA. Audit logging from v1.0. Incident response runbook by v1.1. | Week 1 + Month 1 |
| **Maintenance team undersizing** | Plan for 1-2 engineers shipping v1.0; need 2-3 by month 4 on maintenance. Runaway support tickets. | Hire 2nd engineer month 2, 3rd by month 4. Document runbooks early. Community triage (GitHub issues). | Month 2-4 |
| **Dependency update avalanche** | v1.0 ships with React 19, TypeScript 5.4, Rust 1.80. All update quarterly. One breaks build = support storm. | Automated scanning (Dependabot). Version pinning strategy. Deprecation windows (6 months). Quarterly update cadence. | Week 1 + ongoing |
| **Institutional deployments fail** | 60% of LMS deployment failures stem from: firewall, LTI mismatches, missing JWT claims, proxy timeouts, DNS. | Pre-flight checklist. LTI error messages name exact missing claim. Troubleshooting guide covering top 10 issues (covers 80% support tickets). | Month 4 (v1.1) |
| **Real-world locales / character encoding** | Users in China, India, UAE → UTF-8 issues, locale-specific errors, digit rendering. Not caught in US-only testing. | Test with non-ASCII usernames, Arabic RTL text. Use PostgreSQL with UTF-8 from day 1. Mock non-English locales in QA. | Month 3 (pre-launch) |
| **Windows + macOS dev setup** | Rust dev on Windows = MSVC linker errors. Mac M1 = compilation takes 2x longer. Linux devs assume Unix paths. | Provide setup scripts for Windows/Mac. Docker Compose works everywhere (no native dev required). CI tests on all three OSes. | Week 2 |

---

## 14. Critical Success Factors

1. **Security first**: Implement MFA, audit logging, FERPA compliance in v1.0 (not v1.1). Canvas breach proves this is table-stakes.

2. **DX beats features**: Invest in error messages, docs, troubleshooting guide in v1.0. Users care 3x more about "this just worked" than "this has all features."

3. **Deployment realism**: Kubernetes Operator is mandatory for institutional adoption. Plan 4+ weeks for v1.1.

4. **Content is the moat**: 83 expertly-authored topics (with teaching explanations) are worth 10x the codebase. Hire writers, don't rush content.

5. **Institutional adoption requires v1.1**: Institutions won't deploy until LTI + SCORM + reporting exist. Plan marketing / sales for month 5+.

6. **Maintenance scales linearly**: Plan to 2-3 engineers by month 4. Support tickets ∝ users. Document everything.

7. **Performance is a v1.0 problem**: Test with 1K concurrent users before shipping. One missing index = 1000x slowdown discovered in production = bad.

---

## 15. Monetization & Sustainability

**Model: 100% Free, Ad-Supported Forever**

- **No paywalls**: All 91 topics, all hands-on labs, all gamification, all certificates — completely free
- **No premium tiers**: No upsells, no "pro" features, no freemium model
- **No subscription**: No monthly/yearly charges, ever
- **Revenue**: Ethical Ads (open source friendly ad network) only (non-intrusive sidebar + banner ads)
- **Philosophy**: Learning should never be gatekept. Ads sustain the platform while keeping it free for everyone
- **Ads placement**: Sidebar (topic recommendations), banner (between sections), NOT in quiz/lab areas (distraction-free learning)

**Sustainability**:
- Platform designed to run lean (minimal hosting costs with self-hosted Docker/Kubernetes on any open cloud (AWS, Hetzner, DigitalOcean, bare metal))
- Ad revenue covers infrastructure + 1-2 engineers for maintenance/support
- Open-source community contributions welcome (GitHub contributions)
- No VC pressure, no exit strategy — just a free resource that works

---

## 16. Critical Files for Implementation

- `/apps/api/src/graph/mod.rs` — DAG traversal, lock/unlock evaluation, Cytoscape coordinates
- `/apps/api/src/routes/progress.rs` — Quiz scoring, `newly_unlocked` computation, XP ledger
- `/apps/api/migrations/` — PostgreSQL schema migrations via sqlx
- `/apps/api/src/db/mongo.rs` — MongoDB connection, topic/lab content queries
- `/apps/web/app/topics/[slug]/quiz/page.tsx` — Quiz runner state machine, teaching explanations
- `/apps/web/app/topics/[slug]/labs/page.tsx` — Lab runner, Monaco editor, Xterm.js integration
- `/apps/web/components/graph/KnowledgeMap.tsx` — Cytoscape.js canvas + unlock animation
- `/apps/web/components/gamification/GamificationHub.tsx` — XP, badges, streaks, levels UI
- `/apps/web/components/certificates/CertificateDownload.tsx` — PDF certificate generation + sharing
- `/content/schema/topic.schema.json` — JSON Schema contract for all MDX frontmatter
- `/scripts/validate-content.ts` — Cycle detection + schema validation + jargon checking
- `/scripts/seed-topics.ts` — Idempotent MongoDB + PostgreSQL seeder
