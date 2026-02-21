# Micron NUS-ISE Business Analytics Case Competition 2026 — Question

---

## Contents

- [Introduction](#introduction)
- [Background](#background)
- [Disclosure](#disclosure)
- [Challenge](#challenge)
  - [Question 1](#question-1)
  - [Question 2](#question-2)

---

## Introduction

Micron Technology, a global leader in memory and storage solutions, is accelerating its expansion to meet surging demands across AI, 5G Technology, and Data Centers. The company has outlined a comprehensive roadmap to address the future memory demand over the next decade by investing over $150 billion globally in manufacturing and R&D. This strategy includes major investments in the U.S, such as new DRAM fabs in Idaho and New York, and extends internationally with a next-generation DRAM fab in Japan, and a high-bandwidth memory (HBM) advanced packaging facility in Singapore. These initiatives aim to strengthen global memory supply chains, advance cutting-edge DRAM, NAND and HBM technologies, and generate over 90,000 jobs worldwide.

### Demand Dynamics

Micron's expansion is driven by several critical market forces:

- **Artificial Intelligence (AI):** The rapid growth in AI applications, particularly in data centers, has significantly increased the demand for high-performance memory solutions.
- **5G Technology:** The expansion of 5G networks is boosting the need for advanced memory and storage solutions in smartphones and other connected devices.
- **Data Centers:** With the rise of cloud computing, big data, and AI workloads, data centers require more robust and efficient memory solutions.

---

## Background

### Market Trends

Micron operates in a dynamic semiconductor market where memory demand is heavily influenced by emerging technologies such as AI, 5G Technology, and Data Centers. Micron effectively manages the supply-demand balance by leveraging AI server demand and supply reductions to drive pricing improvements. The company has also seen increased interest from customers in securing long-term agreements due to expectations of tight supply and rising prices.

### Problem Statement

Despite these strong market drivers, Micron faces several significant challenges which can be summarized into the following:

1. **Cyclical Demand:** The semiconductor industry is known for its cyclical demand, where periods of high demand can be followed by oversupply. This volatility affects Micron's revenue and profitability.
2. **Geopolitical Tensions:** Global political issues, such as trade restrictions and export controls, can impact Micron's operations and market access. These tensions can disrupt supply chains and affect the availability of critical materials.
3. **Intense Competition:** Micron competes with major players like Samsung, SK Hynix, and Western Digital. This competition requires continuous investment in research and development to stay ahead in terms of technology and innovation.
4. **Technological Evolution:** Rapid advancements in technology necessitate significant capital investment. Micron must continuously innovate to keep pace with emerging technologies like AI, IoT, and 5G, which drive demand for advanced memory solutions.
5. **Supply Chain Complexity:** The semiconductor supply chain is complex and can be affected by various factors, including natural disasters, pandemics, and logistical challenges. Ensuring a stable supply chain is crucial for Micron's operations.

In this Business Analytics Case Competition, participants will design strategies to optimize manufacturing capability under real-world constraints, ensuring operational efficiency to sustainably navigate the industry's cyclical nature, while preserving the company's competitive edge and maximize profitability.

---

## Disclosure

For avoidance of doubt, all figures and numbers used in the questions provided are strictly arbitrary and have no reference whatsoever to Micron Technology, Inc.

---

## Glossary of Definitions and Calculations

| Attribute | Definition |
|---|---|
| **Quarter** | A 13-week period, with 4 quarters per calendar year. |
| **Loading** | Weekly wafer starts scheduled at the fab for a given node; held constant across all weeks in a quarter. Example: "5,000 wafers for Node 2 in Q1'26" means 5,000 wafers start each week for 13 weeks → 65,000 wafers in Q1'26. |
| **Tool Requirement** | Number of tools required to produce a specified loading at a workstation. Formula: `Tool Requirement = Σ (Loading · RPT) / (7 · 24 · 60 · Utilization)` *(Loading in wafers/week; RPT in minutes/wafer; Utilization as a percentage decimal)* |
| **Tool Available** | The number of existing operational tools installed in a fab for a given workstation. |
| **RPT** | Recipe Processing Time – Number of minutes required to complete a process step on the specified workstation. |
| **TOR** | Tool of Record – Designated, latest-generation tool configuration best suited for executing a specific process step. Typically faster RPT and higher performance, with higher CapEx. |
| **Mintech** | Legacy / older-generation tool configurations capable of executing specific process steps but are not the TOR. Typically slower RPT and lower performance, with lower CapEx. |
| **Utilization** | Percentage of time a workstation tool is available and can be actively used for production. |
| **CapEx requirement** | Total Capital Expenditure: Number of tools purchased × CapEx per tool per workstation. |
| **OpEx requirement** | Total operational expenditure to sustain production (e.g., cross-fab transfers, move-out costs). |
| **Cross-Fab Transfers** | Transferring wafers from one site to another that has the necessary workstation capability to complete the required process steps. |

---

## Challenge

## Question 1

Due to surging demand from AI applications requiring high memory capacity, Micron must significantly increase production of its newest generation of products. As building a new fab is a multi-year process, the immediate priority is to enable additional production capacity within Micron's current facilities despite space constraints.

Your role as an Industrial Engineer is to develop a production and tool purchase strategy that meets the projected wafer loading summarized in Table 1, while operating within existing fab space constraints and minimizing total cost. This case assesses participants' ability to apply optimization techniques and core industrial engineering skills to real-world planning challenges.

Loading here refers to the quantity of wafers that need to be produced per week, staying constant throughout 13 weeks in each quarter.

**Table 1: Summary of projected wafer loading per week across 2026 to 2027 (breakdown per quarter)**

| Quarter | Q1'26 | Q2'26 | Q3'26 | Q4'26 | Q1'27 | Q2'27 | Q3'27 | Q4'27 |
|---|---|---|---|---|---|---|---|---|
| Node 1 | 12000 | 10000 | 8500 | 7500 | 6000 | 5000 | 4000 | 2000 |
| Node 2 | 5000 | 5200 | 5400 | 5600 | 6000 | 6500 | 7000 | 7500 |
| Node 3 | 3000 | 4500 | 7000 | 8000 | 9000 | 11000 | 13000 | 16000 |

The details of each product's production specification, including process steps, required workstations, and processing time are provided in Tables 2(a)–(c).

**Breakdown definition of columns:**
- **Step Name:** Sequence of steps that a wafer needs to run through, all must be completed in order.
- **WS:** Workstation that the step can be run on; each WS consists of identical tools.
- **RPT:** The number of minutes a workstation needs to complete a step.
- **TOR:** Newest generation of tools to run a step, often with faster RPT.

*For example, step 1 for node 1 runs 14 mins per wafer on WS D while 12 mins per wafer on the TOR D+.*

**Table 2(a): Table of recipe requirements for Node 1**

| Step Name | WS | RPT (min) | WS (TOR) | RPT (TOR) |
|---|---|---|---|---|
| Step 1 | D | 14 | D+ | 12 |
| Step 2 | F | 25 | F+ | 21 |
| Step 3 | F | 27 | F+ | 23 |
| Step 4 | A | 20 | A+ | 16 |
| Step 5 | F | 12 | F+ | 9 |
| Step 6 | D | 27 | D+ | 21 |
| Step 7 | D | 17 | D+ | 13 |
| Step 8 | A | 18 | A+ | 16 |
| Step 9 | A | 16 | A+ | 13 |
| Step 10 | D | 14 | D+ | 11 |
| Step 11 | F | 18 | F+ | 16 |

**Table 2(b): Table of recipe requirements for Node 2**

| Step Name | WS | RPT (min) | WS (TOR) | RPT (TOR) |
|---|---|---|---|---|
| Step 1 | F | 19 | F+ | 16 |
| Step 2 | B | 20 | B+ | 18 |
| Step 3 | E | 10 | E+ | 7 |
| Step 4 | B | 25 | B+ | 19 |
| Step 5 | B | 15 | B+ | 11 |
| Step 6 | F | 16 | F+ | 14 |
| Step 7 | F | 17 | F+ | 15 |
| Step 8 | B | 22 | B+ | 16 |
| Step 9 | E | 7 | E+ | 6 |
| Step 10 | E | 9 | E+ | 7 |
| Step 11 | E | 20 | E+ | 19 |
| Step 12 | F | 21 | F+ | 18 |
| Step 13 | E | 12 | E+ | 9 |
| Step 14 | E | 15 | E+ | 12 |
| Step 15 | E | 13 | E+ | 10 |

**Table 2(c): Table of recipe requirements for Node 3**

| Step Name | WS | RPT (min) | WS (TOR) | RPT (TOR) |
|---|---|---|---|---|
| Step 1 | C | 21 | C+ | 20 |
| Step 2 | D | 9 | D+ | 7 |
| Step 3 | E | 24 | E+ | 23 |
| Step 4 | E | 15 | E+ | 11 |
| Step 5 | F | 16 | F+ | 14 |
| Step 6 | D | 12 | D+ | 11 |
| Step 7 | C | 24 | C+ | 21 |
| Step 8 | C | 19 | C+ | 13 |
| Step 9 | D | 15 | D+ | 13 |
| Step 10 | D | 24 | D+ | 20 |
| Step 11 | E | 17 | E+ | 15 |
| Step 12 | E | 18 | E+ | 13 |
| Step 13 | F | 20 | F+ | 18 |
| Step 14 | C | 12 | C+ | 11 |
| Step 15 | D | 11 | D+ | 10 |
| Step 16 | C | 25 | C+ | 20 |
| Step 17 | F | 14 | F+ | 13 |

**Table 3(a): Detailed workstation specifications – Mintech workstations**

| Workstation | A | B | C | D | E | F |
|---|---|---|---|---|---|---|
| Initial tool count for Q1'26 | 85 | 102 | 12 | 50 | 30 | 259 |
| Utilization | 78% | 76% | 80% | 80% | 76% | 80% |
| CapEx per tool | $4.5M | $6.0M | $2.2M | $4.0M | $3.5M | $6.0M |
| Space per tool (m²) | 6.78 | 3.96 | 5.82 | 5.61 | 4.65 | 3.68 |

**Table 3(b): Detailed workstation specifications – TOR workstations**

| Workstation | A+ | B+ | C+ | D+ | E+ | F+ |
|---|---|---|---|---|---|---|
| Initial tool count for Q1'26 | 0 | 0 | 0 | 0 | 0 | 0 |
| Utilization | 84% | 81% | 86% | 88% | 84% | 90% |
| CapEx per tool | $6.0M | $8.0M | $3.2M | $5.5M | $5.8M | $8.0M |
| Space per tool (m²) | 6.93 | 3.72 | 5.75 | 5.74 | 4.80 | 3.57 |

**Table 4: Fab metrics & Overview of Micron's current available tool count**

| Fab | Fab 1 | Fab 2 | Fab 3 |
|---|---|---|---|
| Fab Total Space for tools (m²) | 1500 | 1300 | 700 |
| **Number of Existing Tools per Workstation for Q1'26** | A: 50, B: 25, C: 0, D: 50, E: 40, F: 90 | A: 35, B: 30, C: 0, D: 50, E: 30, F: 60 | A: 0, B: 0, C: 40, D: 35, E: 16, F: 36 |

**Other considerations:**

- **Cross-Fab Transfers:**
  - Executed by transferring wafers from one site to another
  - Receiving site must have the necessary workstation capability to complete the required process steps
  - Cost Required (OpEx): **$50 per wafer per transfer**

- **Tool Move Out:**
  - Discontinuing usage of specified tools and moving them out from the associated fab completely
  - Specified tools are no longer in the tool plan and are not relocated to other sites
  - Executed when a specified tool is no longer required to run any process steps
  - Intended to free up space in the fab
  - Cost Required (OpEx): **$1M per tool**

---

### Part a)

Your production and tool purchase strategy should consist of:

**(i) Completing the Flow Distribution Table** by assigning each process step and loading for every technology node to a specific fab.

*(If numerical results and exact figures cannot be produced, please outline the analytical approach, supporting rationale and expected outcomes.)*

Please note that the loading figures in Table 1 represent wafer counts, and each wafer is required to run through all process steps for its respective technology node. A wafer may be transferred between fabs multiple times as required, with each transfer incurring a Cross-Fab Transfer cost.

**Example Solution Template of the Flow Distribution Table (Table 5):**

| Quarter | Node | Step | Fab | Loading |
|---|---|---|---|---|
| Q2'26 | 1 | 1 | 1 | 5000 |
| Q2'26 | 1 | 1 | 2 | 5000 |
| Q2'26 | 1 | 1 | 3 | 0 |
| … | | | | |
| Q2'26 | 1 | 5 | 1 | 5000 |
| Q2'26 | 1 | 5 | 2 | 5000 |
| Q2'26 | 1 | 5 | 3 | 0 |
| Q2'26 | 1 | 6 | 1 | 0 |
| Q2'26 | 1 | 6 | 2 | 0 |
| Q2'26 | 1 | 6 | 3 | 10000 |
| … | | | | |
| Q2'26 | 1 | 10 | 1 | 0 |
| Q2'26 | 1 | 10 | 2 | 0 |
| Q2'26 | 1 | 10 | 3 | 10000 |

**Example Solution Breakdown:**

- Respective nodes are required to run through all steps:
  - Node 1: 11 steps
  - Node 2: 15 steps
  - Node 3: 17 steps
- For Node 1, Step 1 is allocated to run through 5,000 wafers in Fab 1, 5,000 wafers in Fab 2, and none in Fab 3.
- These 5,000 wafers in each fab continue to run through steps 2–5, then get transported to Fab 3, incurring: `2 fabs × 5,000 wafers × $50/wafer × 13 weeks = $6,500,000` transfer cost over the quarter.
- Once in Fab 3, all 10,000 wafers run through the remaining steps from 6–11.

*Please note that the diagram and table are provided as an example and participants may adopt alternative cut-off strategies or distribution methods where appropriate.*

**(ii) Preparing the Tooling Allocation Plan** by determining the required tool count for each workstation and allocating them across the fabs, considering existing tools and space constraints.

**Example Answer sample for Tool Allocation Plan (Table 6):**

| Quarter \ (WS, Fab) | WS Name | Fab 1 – WS Count | Fab 2 – WS Count | Fab 3 – WS Count |
|---|---|---|---|---|
| WS Component for Q2'26 | A | 10 | 20 | 30 |
| WS Component for Q2'26 | B | 30 | 0 | 0 |

**Constraints and Assumptions to be satisfied:**

1. **All loading requirements must be met:** Every process step must be assigned to a WS with sufficient capacity and no missing steps.
2. **Fab space limits cannot be exceeded:** Total footprint of tools must remain within the fab's available area.
3. **No tool move-outs:** Existing tools must remain in place in this phase.
4. **Cost minimization is expected:** The proposed plan should be optimized for minimal total cost, while meeting all production and space constraints.

---

### Part b)

**(i) Propose an optimization strategy** that allows for tool move-outs and new purchases to meet the projected loading (Table 1) by regenerating the Flow Distribution Table and Tool Allocation Plan as in Part a)(i) and (ii).

Your solution should:
- Meet all loading requirements (no broken capacity)
- Operate within the existing fab space constraints
- Minimize total cost incurred (including cost of cross-fab transfers, move-out activities and new tool purchases)

**(ii) Explain and justify the rationale** behind your proposed production and tool purchase strategy. Your justification should address:
- How the plan meets the projected wafer demand across all technology nodes
- Why the plan is cost-optimal and space-efficient
- Key assumptions (fab constraints, tool capabilities, cost structure)
- Long-term implications for fab flexibility and scalability

---

## Question 2

In the previous question, we assumed a static and absolute loading plan. However, in reality, future demand cannot be predicted with complete accuracy. This creates a challenge as tool purchase orders must be placed 1–2 years in advance due to long lead times. Thus, a tooling plan needs to be finalized even when demand has not been confirmed. Micron's executive team has therefore tasked you with developing a loading design methodology and an accompanying business plan that enables Micron to remain well positioned amid this uncertain market. This case challenges participants' innovative business strategy, strategic insights and business acumen.

### Part a)

There are 3 potential future scenarios depending on how AI demand evolves:

- **Scenario 1 (30%):** AI's development and adoption continue to accelerate, leading to significant increase in required wafer loading.
- **Scenario 2 (50%):** Baseline scenario where AI demand increases at a moderate pace.
- **Scenario 3 (20%):** The AI bubble pops and demand drops significantly.

**Table 7: Mean loadings in each potential scenario**

**Node 1**

| | Q1'26 | Q2'26 | Q3'26 | Q4'26 | Q1'27 | Q2'27 | Q3'27 | Q4'27 |
|---|---|---|---|---|---|---|---|---|
| Scen 1 (30%) | 12000 | 13000 | 13000 | 11000 | 9000 | 6000 | 6000 | 4000 |
| Scen 2 (50%) | 12000 | 10000 | 8500 | 7500 | 6000 | 5000 | 4000 | 2000 |
| Scen 3 (20%) | 12000 | 10000 | 7000 | 4000 | 2000 | 1000 | 0 | 0 |

**Node 2**

| | Q1'26 | Q2'26 | Q3'26 | Q4'26 | Q1'27 | Q2'27 | Q3'27 | Q4'27 |
|---|---|---|---|---|---|---|---|---|
| Scen 1 (30%) | 5000 | 5500 | 6000 | 6500 | 7000 | 8000 | 9000 | 9000 |
| Scen 2 (50%) | 5000 | 5200 | 5400 | 5600 | 6000 | 6500 | 7000 | 7500 |
| Scen 3 (20%) | 5000 | 5000 | 5000 | 4000 | 3000 | 3000 | 2000 | 2000 |

**Node 3**

| | Q1'26 | Q2'26 | Q3'26 | Q4'26 | Q1'27 | Q2'27 | Q3'27 | Q4'27 |
|---|---|---|---|---|---|---|---|---|
| Scen 1 (30%) | 3000 | 4500 | 8000 | 11000 | 14000 | 17000 | 20000 | 23000 |
| Scen 2 (50%) | 3000 | 4500 | 7000 | 8000 | 9000 | 11000 | 13000 | 16000 |
| Scen 3 (20%) | 3000 | 3500 | 4500 | 5500 | 7000 | 8500 | 10000 | 10000 |

Furthermore, even within each scenario, the final realized demand is not certain. For each scenario, the demand in any given quarter follows a **Normal Distribution** with mean loading provided in Table 7, and standard deviation is assumed to be **10% of the mean**. You may assume the scenarios are independent of each other.

**(i)** Calculate the expected loading for each quarter.

**(ii)** Determine the combined variance of the loading for each quarter.

**(iii)** Given that we plan our capacity based solely on Scenario 2, what is the probability that we will be under-capacity for each quarter if Scenario 1 is realized?

---

### Part b)

There is significant opportunity cost involved if we over or under invest in the fab's capacity. Over-investment results in idle capacity, leading to depreciation and maintenance expenses, and cost of capital. Conversely, under-investment restricts output, causing lost revenue and potential erosion of market share to competitors.

Given these trade-offs, what loading should be used as the basis for capacity planning? What should be the recommended capacity planning strategy? Please elaborate and justify your chosen strategy.

You may consider elements such as the probability of meeting potential demand, the relative cost implications of over- versus under-capacity, and concepts like service levels or target probability.

*An exact numerical solution or constructing a full optimization model is not strictly necessary; however, you are expected to provide clear explanation of your analytical approach and reasoning to support your conclusions.*
