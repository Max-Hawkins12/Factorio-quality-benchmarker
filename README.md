# Factorio Quality Upcycler Optimiser


Short 2–3 sentence description.

> Optimizes Factorio 2.1 quality-upcycling systems for either
> Legendary output per input or Legendary output per unit time.

## The Problem

Briefly explain:

- Factorio Quality mechanics
- quality modules and recycling
- why an upcycling loop exists
- machine/module/beacon choices
- the efficiency vs throughput tradeoff

Define the two objectives:

- Legendary / Input
- Legendary / Time

Explain that different upcycling systems may consume different resources,
so Legendary/Input is primarily comparable between configurations of the
same system unless inputs have a common basis.

## How It Works

### 1. Recipe Graph Discovery

Explain:
- ProductionGraph
- UpcyclingGraph
- UpcyclerSystem
- before → upcycler → after combinations

A small hand-written graph/example would help here.

### 2. Machine Configuration Search

Explain:
- machines
- modules
- beacons
- quality tiers
- Pareto pruning

### 3. Graph Optimization

Explain:
- quality-by-quality state evaluation
- Normal → Uncommon → Rare → Epic → Legendary
- material availability constrains downstream recipes
- target-dependent Legendary behaviour
- separate L/Input and L/Time frontiers

### 4. Caching and Pruning

Short section:
- configuration caches
- graph/result caching
- Pareto-frontier pruning
- why exhaustive naive enumeration would be impractical

## Example Results

### Tungsten Plate

#### Direct Self-Upcycling

![Direct Tungsten Upcycling](https://mermaid.ink/img/pako:eNp9kUFPhDAQhf9KMydNYAMutGwPxkSPq1GjF8VsGtoFIrSkW-Ii4b87sC572OicOq9v3nxNe8iMVMBhW5mvrBDWkfVzalNNsB6MrUW1eWl1vnNKbx4r4dR7CgedHHUy6Sl8EN-_Jk-tqErXbV6brMuqUuc48KuRWUPzccmZf0pZq1xpKWx32t6MWy4wbb47J7gcU__Fv-nJrhCN4sSaVkslhz9BTtZC7QfwILelBO5sqzyoFYaPLfTjeAquUDUicDxaJdu9j4SffmYqY1NI9TjfCP1mTH2MQIC8AL4V1Q67tpGId1eK3Ip6Vi2-VNlbRHXAGQ08ULJ0xt4ffm36vCkYeA97tCSLZRKvoiCOQxazJPSgA07pIqQ0XCVsGUQ0YfHgwfdEEiywC7CuoihJGGV0-AGYcrH1?type=png)

| Configuration | Legendary / input craft | Legendary / hour |
| --- | --- | --- |
| Input-optimal | 3.73 Legendary Tungsten Plate / 10,000 Tungsten Plate | 1.74 Legendary Tungsten Plate/h / 5,760 Tungsten Plate/h |
| Throughput-optimal | 2.03 Legendary Tungsten Plate / 10,000 Tungsten Plate | 7.71 Legendary Tungsten Plate/h / 48,447 Tungsten Plate/h |

Short interpretation.

#### Production before upcycling

![Before Tungsten Plate Production](https://mermaid.ink/img/pako:eNqFUk1LxDAQ_SthTgrt0trtVw4i6EVwdRW9aKWEJrbFNinZFHdd-t-ddm1X0dVAIPNm3ps3Q7aQKS6Awkul3rKCaUOu7hKdSILnWumaVel9K_OVETK90eIpgR1KRpQgmsAzse3TCUuXFTMiXWrF28yUSiJtqh9yZJ9D8thwoaqefakHxi4iffRvg1HhYMFAv21ZVZpN-tBkm6wqZY5dPjEyYV_8_KgfVK5ELiRnerPfTNN3O0K1KUe-z4uix73qH6s925JVwRpBiVat5IJ3v6zlcNEPr_vSQqy7sXl_wYJclxyo0a2woBbopQ9h20slYApRo2OKTy14u7ZxoFc7U5XSCSSyQ37D5KNS9SiBZvIC6AurVhi1DceRL0qWa1ZPqMbFCH2Otg1Q1zmJLBC8NEovdj9w-IiDMtAtrIGG0cyL_Hju-L4b-mHkWrABGgQzNwjcOAo9Zx5Eod9Z8D5YcWZROI_jOApczznxYi_uPgDGWfvi?type=png)

| Configuration | Legendary / input craft | Legendary / hour |
| --- | --- | --- |
| Input-optimal | 2.24 Legendary Tungsten Plate / 4,000 Tungsten Ore + 10,000 Molten Iron | 6.44 Legendary Tungsten Plate/h / 11,520 Tungsten Ore/h + 28,800 Molten Iron/h |
| Throughput-optimal | 1.07 Legendary Tungsten Plate / 4,000 Tungsten Ore + 10,000 Molten Iron | 28.1 Legendary Tungsten Plate/h / 112,140 Tungsten Ore/h + 280,350 Molten Iron/h |

Short interpretation.

#### Tungsten ore upcycling → Legendary plate production

![After Tungsten Plate Production](https://mermaid.ink/img/pako:eNqNUl1PwjAU_SvNfdJkkI2xrz4YE30xAUWjLzpDmrVsi1u7lC6ChP_u3WAsEST0pb0np-ece9sNJIoLoLAo1HeSMW3I5CXWsSS4HpUuWTF_rWW6NELOn7T4iGGHkg4liMbwSQaDG_JcsyI36_lblayTIpcp0vcYOWBI7gymqmh0H7SSyNxVpKk6wYlIheRMr_sQVcGMmFda8ToxOVL3Wkfelwqg84HVdzVrWGTW2_SpL9A86311xhFtrjufv_uJ57jdkGXGKkGJVrXkgm9PjPZ_0tHMemomVi0NLEh1zoEaXQsLSoEZmhI2jUQMJhMlpqZ41ILXqwE29TVIVKF0DLHc4v2KyXelyk4CQ6QZ0AUrlljVFce273OWalYeUI3DEfoO4xqgju2OLBA8N0pPd7-1_bStMtANrIAG4dANvWhse54TeEHoWLAG6vtDx_edKAxce-yHgbe14KeNYg_DYBxFUeg7rj1yIzfa_gKDoAu9?type=png)

| Configuration | Legendary / input craft | Legendary / hour |
| --- | --- | --- |
| Input-optimal | 2.33 Legendary Tungsten Plate / 10,000 Tungsten Ore | 21.8 Legendary Tungsten Plate/h / 115,200 Tungsten Ore/h |
| Throughput-optimal | 1.27 Legendary Tungsten Plate / 10,000 Tungsten Ore | 96.4 Legendary Tungsten Plate/h / 968,940 Tungsten Ore/h |

Short interpretation.

### Processing Unit

#### Direct self-upcycling

[graph]

| Configuration | Legendary / input craft | Legendary / hour |
| --- | --- | --- |
| Input-optimal | 15.6 Legendary Processing Unit / 20,000 Electronic Circuit + 2,000 Advanced Circuit + 5,000 Sulfuric Acid | 15.4 Legendary Processing Unit/h / 19,800 Electronic Circuit/h + 1,980 Advanced Circuit/h + 4,950 Sulfuric Acid/h |
| Throughput-optimal | 8.39 Legendary Processing Unit / 20,000 Electronic Circuit + 2,000 Advanced Circuit + 5,000 Sulfuric Acid | 162 Legendary Processing Unit/h / 387,000 Electronic Circuit/h + 38,700 Advanced Circuit/h + 96,750 Sulfuric Acid/h |

Short interpretation.

### Electromagnetic Plant

#### Recycling for constituent Legendary items

[graph]

| Configuration | Legendary / input craft | Legendary / hour |
| --- | --- | --- |
| Input-optimal | 40.3 Legendary Holmium Plate + 13.4 Legendary Steel Plate + 13.4 Legendary Processing Unit + 13.4 Legendary Refined Concrete / 15,000 Holmium Plate + 5,000 Steel Plate + 5,000 Processing Unit + 5,000 Refined Concrete | 545 Legendary Holmium Plate/h + 182 Legendary Steel Plate/h + 182 Legendary Processing Unit/h + 182 Legendary Refined Concrete/h / 202,500 Holmium Plate/h + 67,500 Steel Plate/h + 67,500 Processing Unit/h + 67,500 Refined Concrete/h |
| Throughput-optimal | 22.6 Legendary Holmium Plate + 7.54 Legendary Steel Plate + 7.54 Legendary Processing Unit + 7.54 Legendary Refined Concrete / 15,000 Holmium Plate + 5,000 Steel Plate + 5,000 Processing Unit + 5,000 Refined Concrete | 4,377 Legendary Holmium Plate/h + 1,459 Legendary Steel Plate/h + 1,459 Legendary Processing Unit/h + 1,459 Legendary Refined Concrete/h / 2,902,500 Holmium Plate/h + 967,500 Steel Plate/h + 967,500 Processing Unit/h + 967,500 Refined Concrete/h |

#### Legendary Electromagnetic Plants

[graph]

| Configuration | Legendary / input craft | Legendary / hour |
| --- | --- | --- |
| Input-optimal | 10.8 Legendary Electromagnetic Plant / 150,000 Holmium Plate + 50,000 Steel Plate + 50,000 Processing Unit + 50,000 Refined Concrete | 14.5 Legendary Electromagnetic Plant/h / 202,500 Holmium Plate/h + 67,500 Steel Plate/h + 67,500 Processing Unit/h + 67,500 Refined Concrete/h |
| Throughput-optimal | 6.03 Legendary Electromagnetic Plant / 150,000 Holmium Plate + 50,000 Steel Plate + 50,000 Processing Unit + 50,000 Refined Concrete | 117 Legendary Electromagnetic Plant/h / 2,902,500 Holmium Plate/h + 967,500 Steel Plate/h + 967,500 Processing Unit/h + 967,500 Refined Concrete/h |

Short discussion of the particularly interesting
efficiency/throughput tradeoff.

## Validation

Explain that selected optimizer outputs were reproduced/tested in Factorio.

Potential table:

| System | Optimizer | In-game | Difference |
| --- | ---: | ---: | ---: |
| ... | ... | ... | ... |

Explain any expected modelling/measurement error.

## Running the Optimizer

Requirements.

Installation.

Command(s).

Where results are written.

## Results Data

Explain:

`results.csv`
- one row per optimized system
- both objective-optimal configurations
- metrics under both objectives

`configurations.csv`
- recipe/machine/module/beacon configuration corresponding to result IDs

Link to the files.

## Current Limitations

Keep factual and relatively short:
- mining not yet modelled as an optimization stage
- productivity research not yet modelled
- cross-system resource costs are not reduced to a common resource basis
- efficiency modules are omitted because energy consumption is not an objective
- whatever else is genuinely relevant

## Planned Work

### Code Improvement
- Tests
- Improved results reporting
- performance optimisation
  
### Additional features, in priority order
1. Useful-item analysis and automatic scope discovery - replace the negative `UNCRAFTABLE_ITEMS` approach with `DESIRED_LEGENDARY_ENTITIES`, derive the relevant material subgraph, restrict upcycler discovery accordingly, and recycle irrelevant byproducts.
2. Mining optimisation/scaling - evaluate mining configurations, mining productivity and output constraints, then scale applicable systems from raw-resource production.
3. Productivity research scaling - incorporate research levels into recipe configuration generation and optimisation.


- mining
- productivity research
- broader/exhaustive item evaluation
- performance/testing improvements
- static results viewer











