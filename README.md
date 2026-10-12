# Factorio Quality Upcycler Optimiser

Factorio Quality Upcycler Optimiser is a Python optimisation tool for finding efficient ways to produce Legendary-quality items using [Factorio: Space Age's](https://store.steampowered.com/app/645390/Factorio_Space_Age/) Quality and Recycler mechanics. It discovers valid production and upcycling graphs, then searches combinations of machines, modules, and beacons to independently optimise them for resource efficiency and production throughput.

The optimiser models upcycling as a graph of recipes evaluated across Factorio's five quality levels. Pareto-frontier pruning and caching are used to make the large configuration search tractable.

## The Problem

### How Does Quality Work?

Factorio's Space Age expansion introduces four quality levels above the standard Normal quality: Uncommon, Rare, Epic, and Legendary. Higher-quality entities receive bonuses to relevant attributes, such as a crafting machine's crafting speed, a module's effects, or a container's storage capacity. As a result, producing large quantities of Legendary items can provide significant benefits to a late-game factory.

Quality modules can be inserted into compatible machines to give crafted items a chance of being produced at a higher quality. Increasing the quality effect improves this chance, but producing Legendary items remains probabilistic and typically requires processing a large quantity of lower-quality material.

Recipes can be crafted using higher-quality ingredients, but all non-fluid ingredients must have the same quality. Fluids are quality-agnostic: they cannot themselves have quality, but can be used when crafting a recipe at any quality level.

Read more about the quality mechanic on the [Factorio Wiki](https://wiki.factorio.com/Quality).

### What is an Upcycler?

Because quality improvements are probabilistic, producing higher-quality items also produces large quantities of unwanted lower-quality items. The Recycler provides a way to recover and repeatedly process these items.

For most recipes, recycling an item returns its ingredients with a total expected yield of 25% of the ingredients required to craft it. Items without a suitable reversible recipe can instead recycle into themselves at 25% yield. For example:

```text
1 Processing Unit -> 5 Electronic Circuits + 0.5 Advanced Circuits
1 Iron Plate -> 0.25 Iron Plate
```

When a Recycler contains quality modules, its recycled outputs also have a chance to increase in quality. These outputs can then be crafted or recycled again, repeatedly discarding material while progressively moving some of it through: Normal → Uncommon → Rare → Epic → Legendary

This repeated crafting and recycling process is referred to here as upcycling. An upcycling system can be as simple as repeatedly recycling an item into itself, or can involve crafting the item into a more expensive intermediate before recycling it back into useful ingredients.

### Why the Optimiser?

Choosing an effective upcycling configuration involves several competing
effects:

- Quality modules increase the probability of producing higher-quality items, but reduce machine speed.
- Speed modules increase processing throughput, but reduce the quality effect of the machine.
- Productivity modules produce additional output from the same input materials, but also affect machine speed.
- Beacons allow additional module effects to be applied to machines, with diminishing effectiveness as more beacons are added.

A configuration that maximises the probability of quality improvements is therefore not necessarily the configuration that produces Legendary items fastest. Likewise, maximising throughput can consume substantially more input material for each Legendary item produced.

The optimiser treats these as two independent objectives:

Legendary / Input measures resource efficiency: the expected Legendary output produced from a fixed quantity of initial input.

Legendary / Time measures throughput: the expected number of Legendary items produced per unit time while accounting for the sustainable processing rate of the complete upcycling system.

For each valid upcycling system, the optimiser searches for configurations that maximise each objective independently. This makes it possible to compare the most resource-efficient solution with the maximum-throughput solution and quantify the trade-off between them.

## How It Works

The optimiser separates the problem into two parts: discovering possible upcycling systems and finding the best configuration of modules for each recipe in the system.

### Upcycler System Discovery

Factorio recipes are represented as directed graphs connecting input materials, recipes, and output materials. The optimiser searches these relationships to discover two types of graph:

- **Production graphs** transform a set of materials into a single item through a sequence of recipes.
- **Upcycling graphs** contain the recycling loop responsible for repeatedly processing an item through the quality levels.

These graphs can then be combined into an **upcycling system**, consisting of an upcycling graph with optional production stages before and after it.

For example, Legendary Tungsten Plates can be produced using several different systems:

```text
Tungsten Plate
    → Quality Upcycling of Tungsten Plate
    → Legendary Tungsten Plate

Tungsten Ore + Molten Iron
    → Tungsten Plate Production
    → Quality Upcycling of Tungsten Plate
    → Legendary Tungsten Plate

Tungsten Ore
    → Quality Upcycling of Tungsten Ore
    → Legendary Tungsten Plate Production (+ Molten Iron)
    → Legendary Tungsten Plate
```

This allows the optimiser to compare fundamentally different approaches rather than optimising only a single predefined recycling loop.

### Configuration Search and Pruning

Each recipe can be executed using many possible combinations of machine, modules, and beacons. Enumerating every combination at every stage of every graph would make the complete search prohibitively large. Only Legendary machines and modules need to be considered, as they dominate their lower-quality equivalents for the attributes relevant to the optimisation.

Instead, the optimiser first generates valid beacon and machine configurations and calculates their combined effects on crafting speed, productivity, and quality chance. These configurations are then used to construct recipe configurations, which form the choices considered during graph optimisation.

Dominated configurations are removed using **Pareto-frontier pruning**. A configuration is discarded when another configuration is at least as good in every relevant metric and strictly better in at least one.

The resulting frontiers contain only configurations representing potentially useful trade-offs, substantially reducing the number of combinations considered during graph optimisation.

![Configuration Hierarchy](https://mermaid.ink/img/pako:eNqVUjtvgzAQ_ivoZoh4GYKHqmoqdWmWjK07WPgCqIDRBdS0KP-9xiRtFWUoliz77vP30Mkj5FohcNjX-iMvJfXO806QaKftmLXVaqgxcDzvznlAmesrJLTIVuZl1eIFmh_eQs6lhXaYV90PMlcWeCLZlTdCvAo4K88NZ6PbfVUMJPtKtwcBb_ejcyhlh9whPbQK1ekqrZG4RFiuMZv_plhiP5v-sV9AnkdjuOcZLaDaURqmPf9DBBcKqhTwngZ0oUFq5FTCOAkK6EtsUAA3V0I1HD0l6d3Lda1JgGgnfifbF62bi4RRLkrge1kfTDV0Svb4WMmCZPPTJTTmtDEZeuABixIXUFW9pu38O-0ntcrARzgCj-NVGsfBOon9IErSIHPhEzgL2SqLojBMWZT5SchOLnzZKP5qzeKIxVnGWJqEfpScvgHoDPyA?type=png)

### Quality-by-Quality Graph Optimisation

An upcycling graph cannot be optimised one recipe at a time. The configuration chosen for one recipe changes both the quantity and quality distribution of material available to every later recipe.

The optimiser therefore evaluates the complete graph while maintaining a state containing the material currently available at each quality level.

The graph is evaluated sequentially through: Normal → Uncommon → Rare → Epic → Legendary

At each quality level, the optimiser considers the relevant recipe configurations, calculates their material consumption and production, and propagates the resulting state through the graph. Recipe throughput is constrained by the materials available in the current state, ensuring that downstream recipes cannot consume more of a particular quality than upstream stages have produced.

Each possible recipe configuration can produce a new candidate state. Rather than retaining every possible combination, dominated states are discarded after each stage, retaining a frontier of non-dominated candidate states for subsequent optimisation stages. States that cannot lead to a better solution are removed using further Pareto-frontier pruning.

Legendary items require special handling: once the target item reaches Legendary quality it becomes a terminal output rather than being recycled again. This behaviour is target-dependent, allowing the same underlying graph to be optimised for different Legendary outputs.

### Optimisation Objectives

Each discovered upcycling system is optimised independently for two objectives.

**Legendary / Input** maximises the expected target Legendary output from a fixed initial input. Machine speed is irrelevant to this objective; the optimiser instead searches for the combination of quality and productivity effects that extracts the greatest Legendary yield from the supplied material.

**Legendary / Time** maximises sustainable target Legendary production throughput. This introduces machine speed and system utilisation into the optimisation and allows speed to be traded against quality when doing so increases overall Legendary production. The optimiser calculates this internally as Legendary items per second, while results are presented as Legendary items per hour for readability.

The resulting configurations can therefore be substantially different. A resource-efficient configuration may favour quality and productivity, while a throughput configuration can sacrifice some quality chance in exchange for processing material much faster.

### Caching

Machine, recipe, graph, and result calculations are cached throughout the search. Many recipes and configurations are shared between different upcycling systems, so previously calculated frontiers can be reused rather than recomputed.

Combined with Pareto-frontier pruning, this reduces a large combinatorial search to a tractable set of candidate configurations.

## Example Results

The following results represent theoretical expected production rates under the optimiser's current modelling assumptions. All configurations use Legendary-quality machines and modules, with inherent machine productivity and productivity research excluded. Throughput is normalised to the processing capacity of the initial machine, rather than representing a fully scaled factory with integer machine counts.

The examples demonstrate different upcycling strategies and the trade-offs between resource efficiency and throughput. As the systems may require different input materials, their results are not necessarily directly comparable on an equal-resource basis.

All results for Tungsten Plate, Processing Unit, and Electromagnetic Plant can be found in [`data/results/results.csv`](data/results/results.csv), with the recipe configurations for each graph in [`data/results/configurations.csv`](data/results/configurations.csv).

I have included a further breakdown of some designs:

### Tungsten Plate

#### Tungsten Plate Self-Upcycling

![Direct Tungsten Upcycling](https://mermaid.ink/img/pako:eNp9kUFPhDAQhf9KMydNYAMutGwPxkSPq1GjF8VsGtoFIrSkW-Ii4b87sC572OicOq9v3nxNe8iMVMBhW5mvrBDWkfVzalNNsB6MrUW1eWl1vnNKbx4r4dR7CgedHHUy6Sl8EN-_Jk-tqErXbV6brMuqUuc48KuRWUPzccmZf0pZq1xpKWx32t6MWy4wbb47J7gcU__Fv-nJrhCN4sSaVkslhz9BTtZC7QfwILelBO5sqzyoFYaPLfTjeAquUDUicDxaJdu9j4SffmYqY1NI9TjfCP1mTH2MQIC8AL4V1Q67tpGId1eK3Ip6Vi2-VNlbRHXAGQ08ULJ0xt4ffm36vCkYeA97tCSLZRKvoiCOQxazJPSgA07pIqQ0XCVsGUQ0YfHgwfdEEiywC7CuoihJGGV0-AGYcrH1?type=png)

| Configuration | Legendary / input craft | Legendary / hour |
| --- | --- | --- |
| Input-optimal | 3.73 Legendary Tungsten Plate / 10,000 Tungsten Plate | 1.74 Legendary Tungsten Plate/h / 5,760 Tungsten Plate/h |
| Throughput-optimal | 2.06 Legendary Tungsten Plate / 10,000 Tungsten Plate | 7.72 Legendary Tungsten Plate/h / 47,819 Tungsten Plate/h |

Direct self-upcycling is the simplest form of upcycling, where Normal-quality Tungsten Plates are repeatedly recycled until they reach Legendary quality.

The input-optimal configuration uses four Legendary Quality Module 3s at every quality level, maximising the chance of quality improvements. However, the throughput-optimal configuration introduces 11 beacons containing a combination of Legendary Speed Module 1s and a Speed Module 2 when recycling Normal-quality plates. This increases Legendary production from 1.74 to 7.72 plates per hour, approximately 4.4 times the throughput, while sacrificing around 45% of the resource efficiency. This demonstrates how the optimal configuration changes when prioritising processing speed over material efficiency.

#### Tungsten Plate Production Before Upcycling

![Before Tungsten Plate Production](https://mermaid.ink/img/pako:eNqFUk1LxDAQ_SthTgrt0trtVw4i6EVwdRW9aKWEJrbFNinZFHdd-t-ddm1X0dVAIPNm3ps3Q7aQKS6Awkul3rKCaUOu7hKdSILnWumaVel9K_OVETK90eIpgR1KRpQgmsAzse3TCUuXFTMiXWrF28yUSiJtqh9yZJ9D8thwoaqefakHxi4iffRvg1HhYMFAv21ZVZpN-tBkm6wqZY5dPjEyYV_8_KgfVK5ELiRnerPfTNN3O0K1KUe-z4uix73qH6s925JVwRpBiVat5IJ3v6zlcNEPr_vSQqy7sXl_wYJclxyo0a2woBbopQ9h20slYApRo2OKTy14u7ZxoFc7U5XSCSSyQ37D5KNS9SiBZvIC6AurVhi1DceRL0qWa1ZPqMbFCH2Otg1Q1zmJLBC8NEovdj9w-IiDMtAtrIGG0cyL_Hju-L4b-mHkWrABGgQzNwjcOAo9Zx5Eod9Z8D5YcWZROI_jOApczznxYi_uPgDGWfvi?type=png)

| Configuration | Legendary / input craft | Legendary / hour |
| --- | --- | --- |
| Input-optimal | 15.1 Legendary Tungsten Plate / 40,000 Tungsten Ore + 100,000 Molten Iron | 3.82 Legendary Tungsten Plate/h / 10,080 Tungsten Ore/h + 25,200 Molten Iron/h |
| Throughput-optimal | 7.19 Legendary Tungsten Plate / 40,000 Tungsten Ore + 100,000 Molten Iron | 20.1 Legendary Tungsten Plate/h / 111,919 Tungsten Ore/h + 279,799 Molten Iron/h |

This system introduces a production stage, crafting Tungsten Plates from Tungsten Ore and Molten Iron before recycling them.

The input-optimal configuration uses a combination of productivity and quality modules in the Foundry, while the throughput-optimal configuration favours quality modules supported by speed beacons. Both configurations continue to prioritise quality modules during recycling.

Interestingly, the input-optimal yield is almost identical to direct self-upcycling when normalised to equivalent quantities of Tungsten Plates. However, the addition of the production stage substantially changes the achievable throughput, demonstrating how the structure of an upcycling system influences its performance.

#### Tungsten Ore Upcycling → Legendary Plate Production

![After Tungsten Plate Production](https://mermaid.ink/img/pako:eNqNUl1PwjAU_SvNfdJkkI2xrz4YE30xAUWjLzpDmrVsi1u7lC6ChP_u3WAsEST0pb0np-ece9sNJIoLoLAo1HeSMW3I5CXWsSS4HpUuWTF_rWW6NELOn7T4iGGHkg4liMbwSQaDG_JcsyI36_lblayTIpcp0vcYOWBI7gymqmh0H7SSyNxVpKk6wYlIheRMr_sQVcGMmFda8ToxOVL3Wkfelwqg84HVdzVrWGTW2_SpL9A86311xhFtrjufv_uJ57jdkGXGKkGJVrXkgm9PjPZ_0tHMemomVi0NLEh1zoEaXQsLSoEZmhI2jUQMJhMlpqZ41ILXqwE29TVIVKF0DLHc4v2KyXelyk4CQ6QZ0AUrlljVFce273OWalYeUI3DEfoO4xqgju2OLBA8N0pPd7-1_bStMtANrIAG4dANvWhse54TeEHoWLAG6vtDx_edKAxce-yHgbe14KeNYg_DYBxFUeg7rj1yIzfa_gKDoAu9?type=png)

| Configuration | Legendary / input craft | Legendary / hour |
| --- | --- | --- |
| Input-optimal | 1.86 Legendary Tungsten Plate / 10,000 Tungsten Ore | 17.4 Legendary Tungsten Plate/h / 115,200 Tungsten Ore/h |
| Throughput-optimal | 1.03 Legendary Tungsten Plate / 10,000 Tungsten Ore | 77.2 Legendary Tungsten Plate/h / 956,385 Tungsten Ore/h |

Rather than upcycling Tungsten Plates directly, this system first recycles Tungsten Ore to Legendary quality before crafting the final plates.

Both optimal configurations use maximum-quality recycling for Uncommon through Epic ore, with the throughput-optimal configuration introducing speed beacons at Normal quality. The final Legendary plate production uses productivity modules and speed beacons, as quality modules provide no benefit when crafting with Legendary ingredients.

This system achieves the highest throughput of the three Tungsten Plate examples, producing 77.2 Legendary Plates per hour. It demonstrates the potential advantage of upcycling an intermediate material rather than the target item itself, although different input requirements prevent a direct resource-efficiency comparison.

### Processing Unit

#### Processing Unit Self-Upcycling

![Self Production Upcycling](https://mermaid.ink/img/pako:eNqNkk1v2zAMhv-KwLMT2HX8ER2GFt0OAzp0W9HL5h4EibGF2ZJBS1uywP-9srukSYsWEyBA5KuHpF5oD9IqBA6b1v6RjSDHbr5XVBkW1mfTe5ewxeID-0pWeem0NWfixXti-ob4nJkv3PdyJ1tt6oN-TMzyrXfTFJN42M-z_azgU4vSkTVasmtN0mtXwcPlng2N6JEzst4oVOP52IG7Ur-Fkaj-n0oDdefbjafQ60pq9S5yfEWgvnnRarc7eeop2eB2fO1NwEIgcRgmJ-6NdqdWwsOB-OdPuH6DNRolaMdegGfdBieU9h2bW0IENWkF3JHHCDqkTkwh7KfiFbgGO6yAhyOh8ttFKP9rIW1rqYLKjIHvhflhbXcoEWyoG-Ab0Q4h8r0SDj9qUZPojlkKYyJdB8Mc8CRO8whQaWfpy9NfnL_kXBn4HrbAi3KZltl6FWdZUmRFmUSwA57nyyTPk3VZpPEqL4tsjODvPEq8LIvVOqw4zuM0WcXJ-AhSYPdV?type=png)

| Configuration | Legendary / input craft | Legendary / hour |
| --- | --- | --- |
| Input-optimal | 7.46 Legendary Processing Unit / 20,000 Electronic Circuit + 2,000 Advanced Circuit + 5,000 Sulfuric Acid | 7.38 Legendary Processing Unit/h / 19,800 Electronic Circuit/h + 1,980 Advanced Circuit/h + 4,950 Sulfuric Acid/h |
| Throughput-optimal | 3.52 Legendary Processing Unit / 20,000 Electronic Circuit + 2,000 Advanced Circuit + 5,000 Sulfuric Acid | 72.7 Legendary Processing Unit/h / 412,749 Electronic Circuit/h + 41,275 Advanced Circuit/h + 103,187 Sulfuric Acid/h |

Unlike simple self-recycling, this system repeatedly crafts and recycles Processing Units, recovering their constituent Electronic Circuits and Advanced Circuits to produce higher-quality ingredients for subsequent crafting.

The input-optimal configuration combines productivity and quality modules during crafting, while using maximum-quality modules for recycling. The throughput-optimal configuration instead introduces speed beacons at Normal quality and uses maximum-quality modules in the initial crafting stage.

This demonstrates how the optimiser balances productivity, quality improvements, and processing speed across multiple interconnected recipes. The throughput-optimal configuration produces approximately 9.8 times as many Legendary Processing Units per hour, but with substantially greater material consumption.

#### Electromagnetic Plant Recycling for Legendary Processing Units

![Electromagnetic Plants for Processing Units](https://mermaid.ink/img/pako:eNqNk19r2zAUxb-Kuc9OsOP_fhiDbtBCy7qOvmzug5BubFFZMrLEkgV_98neksYMuzMYpHv8O746F52AKoZQwl6on7Qh2nj3T5WupOeeO9lZE3qbzQfvUStmqeFKzsTdmhitifGC-FaZPnju6JEKLuuzfilM8hdrxhbXxN2aGK2J8Sie37c8flRwq0TLbes9CmKwgpePJ69vSIelp5WVDNkwT8kh3wyi-F8gcoALgmLfjy09S27eh2IHPeGeS2TejZJU4zu_upzZgV8tEdwcr_K-Jhs8DP8OyGGfBVKjVUtqiYbT8XzSXE8VXs7c31E56B5rlIzoo7ecY28IG5Vhju9m-FKmC3A0g9fyXTCIZwarWV8cwIdacwal0RZ9aFG3ZNzCaXSuwDTYOrR0S43MHjbO-3VDlVC6gkqOfEfkd6Xas4UbY91AuSeidzvbMXf8T5zUmrSXqnY9or5xAzdQhkEc-ICMG6Uf_tz26dJPzlCe4ABllm-jPCniIEnCLMny0IcjlGm6DdM0LPIsCuI0z5LBh19TK8E2z-KiKPI0DMZVOvwGrBVv3w?type=png)

| Configuration | Legendary / input craft | Legendary / hour |
| --- | --- | --- |
| Input-optimal | 15.4 Legendary Holmium Plate + 5.13 Legendary Steel Plate + 5.13 Legendary Processing Unit + 5.13 Legendary Refined Concrete / 15,000 Holmium Plate + 5,000 Steel Plate + 5,000 Processing Unit + 5,000 Refined Concrete | 208 Legendary Holmium Plate/h + 69.3 Legendary Steel Plate/h + 69.3 Legendary Processing Unit/h + 69.3 Legendary Refined Concrete/h / 202,500 Holmium Plate/h + 67,500 Steel Plate/h + 67,500 Processing Unit/h + 67,500 Refined Concrete/h |
| Throughput-optimal | 8.37 Legendary Holmium Plate + 2.79 Legendary Steel Plate + 2.79 Legendary Processing Unit + 2.79 Legendary Refined Concrete / 15,000 Holmium Plate + 5,000 Steel Plate + 5,000 Processing Unit + 5,000 Refined Concrete | 1,678 Legendary Holmium Plate/h + 559 Legendary Steel Plate/h + 559 Legendary Processing Unit/h + 559 Legendary Refined Concrete/h / 3,008,408 Holmium Plate/h + 1,002,803 Steel Plate/h + 1,002,803 Processing Unit/h + 1,002,803 Refined Concrete/h |

An alternative approach to obtaining Legendary Processing Units is to craft and recycle Electromagnetic Plants, recovering their constituent materials at progressively higher qualities.

Unlike the previous examples, this system produces multiple useful Legendary outputs simultaneously: Holmium Plates, Steel Plates, Processing Units, and Refined Concrete. The input-optimal configuration prioritises quality modules throughout the system, while the throughput-optimal configuration introduces speed beacons during Normal-quality processing and uses speed modules when processing Legendary items.

This demonstrates the optimiser's ability to track multiple Legendary outputs from the same recycling system. However, the additional materials required to craft Electromagnetic Plants make resource-efficiency comparisons with direct Processing Unit upcycling more complicated.

### Electromagnetic Plant

#### Electromagnetic Plant Self-Upcycling

![Electromagnetic Plants for Themself](https://mermaid.ink/img/pako:eNqNkt2O0zAQhV_Fmuu0qlvnp75ASAsSSItYFu0NZC8se5pYOHbk2KKlyrvjBNptBexiyVI8J9_MmbGPIJ1C4LAz7rtshQ_k9r72tSVpvbd9DJQsFq_InXcqyqCdvRLXz4mb50T2D_EpMv_w0MuDNNo2J_0cmOWPMUwWJ_FyP5n_WsM7ZzodO3JnRMAaHl8fydCKHjnxLlqFarxuKSGfA6L5X2CTgORa4jBMth6sDi9DLEH3uNMWFblxVnp8odS57wR-isLocLgYziXZ4n78c5oJe2tQBu860VgMWk792XB5BfB44n7PNUG32KBVwh_IX_GrykMQapr0CBk0XivgwUfMoEPfiekIxyl9DaHFLrXL06dHFfeLVODbQjrjfA21nfhe2C_OdacUaRxNC3wnzJBOsVfpat5o0XjRnaM-GUV_kwYXgNMVYxmg0sH5D7-e-PzS58zAj7AHXlbLTZVv2SrPaZmXFc3gALwolrQo6LYqNytWVGU-ZvBjtrJaViXbpkUZXdNqTdn4E_zOFUo?type=png)

| Configuration | Legendary / input craft | Legendary / hour |
| --- | --- | --- |
| Input-optimal | 4.11 Legendary Electromagnetic Plant / 150,000 Holmium Plate + 50,000 Steel Plate + 50,000 Processing Unit + 50,000 Refined Concrete | 5.54 Legendary Electromagnetic Plant/h / 202,500 Holmium Plate/h + 67,500 Steel Plate/h + 67,500 Processing Unit/h + 67,500 Refined Concrete/h |
| Throughput-optimal | 2.23 Legendary Electromagnetic Plant / 150,000 Holmium Plate + 50,000 Steel Plate + 50,000 Processing Unit + 50,000 Refined Concrete | 44.8 Legendary Electromagnetic Plant/h / 3,008,408 Holmium Plate/h + 1,002,803 Steel Plate/h + 1,002,803 Processing Unit/h + 1,002,803 Refined Concrete/h |

This example uses the same underlying Electromagnetic Plant crafting and recycling system as the previous example, but optimises for Legendary Electromagnetic Plants rather than their constituent materials.

The configurations differ at Legendary quality: instead of recycling the completed plants to recover Legendary ingredients, the target plants are retained as terminal outputs. Both configurations use speed modules and beacons at Legendary quality, while the throughput-optimal configuration also accelerates Normal-quality processing.

This demonstrates an important feature of the optimiser: the same production and recycling graph can be evaluated for different target outputs, with the optimal treatment of Legendary items depending on the selected target.

## Current Limitations

- Inherent machine productivity is not currently modelled. The Biochamber, Electromagnetic Plant, and Foundry normally receive an inherent productivity bonus of 50%. These bonuses are temporarily excluded because the additional material generated substantially increases the number of candidate states considered during graph optimisation. Supporting inherent productivity efficiently will require a redesigned optimisation algorithm.
- Cross-system resource costs are not reduced to a common resource basis. Systems cannot be accurately compared due to requiring different inputs, so inputs should be normalised to common resources.
- Mining not yet modelled as an optimisation stage. Quality modules can be added to mining drills, so when an upcycler takes a raw resource there should be an additional optimisation for the ideal mining drill configuration
- Productivity research not yet modelled. A few items have an associated productivity research, these add a global 10% productivity bonus when crafting this item per level, up to the engine cap of 300%. Therefore, the productivity research level fundamentally changes the optimal configuration as more items can be produced without the need for productivity modules.
- Quality improvements are probabilistic, so the optimiser models expected material flows and Legendary output rather than simulating individual crafting and recycling events. Actual in-game results will vary due to randomness, particularly over smaller production runs, and may differ from the calculated optimal rates. The results therefore represent theoretical long-run averages rather than guaranteed production rates.

## Running the Optimiser

### Requirements

- Python 3.13
- [uv](https://docs.astral.sh/uv/) for dependency and environment management

### Installation

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/Max-Hawkins12/Factorio-quality-benchmarker.git
cd factorio-quality-benchmarker
```

Install the dependencies and create a virtual environment using uv:

```bash
uv sync
```

### Parsing Your Own Raw Data

Parsed game data for Factorio version 2.1.14 is included in the repository, so extracting game data is not required to run the optimiser.

To extract and parse data from your own Factorio installation, follow the instructions in [`data/raw/README.md`](data/raw/README.md).

### Generating Results

From the root, run:

```bash
uv run factorio-quality-benchmarker run
```

This automatically uses the project's virtual environment and installed dependencies.

### Results

The optimiser exports its results to the [`data/results/`](data/results/) directory:

- results.csv — optimised upcycling systems, including their resource-efficiency and throughput metrics.
- configurations.csv — the corresponding machine, module and beacon configurations for each optimised system.

Both files can be inspected independently or used together to examine the configurations responsible for each result.

## Planned Work

The optimiser currently supports discovering and evaluating alternative upcycling systems, but several limitations remain in the accuracy, scalability, and usability of its results. Future development will focus on improving the optimisation algorithm, extending the game mechanics it models, and making the results more accessible to Factorio players.

### Optimisation and Model Improvements

#### 1. Redesign graph optimisation and Pareto-frontier generation

The current optimiser independently maximises Legendary output per input and per second. Although Pareto-frontier pruning substantially reduces the search space, the number of candidate states can still grow rapidly as additional recipes and productivity effects are introduced.

The next major improvement will involve changing how production graphs are scaled and optimised. Currently, each graph is normalised to the processing speed of its first machine, with downstream production constrained by the resulting material availability. A more flexible approach would instead scale the entire system to achieve a specified Legendary output rate, such as 50 Legendary items per hour.

This would allow multiple machines to be used for each recipe, removing the need to maximise the processing speed of individual machines. Consequently, speed modules would generally become unnecessary for minimising resource consumption, as equivalent throughput could be achieved by adding more machines. The optimisation would instead focus on finding the most resource-efficient recipe configurations and balancing their material consumption against the number of machines required.

The revised algorithm would generate a Pareto frontier across two competing objectives:

- Minimum resource consumption: The configuration requiring the fewest input materials to sustain a specified Legendary output rate.
- Minimum machine requirements: The configurations requiring the fewest machines to sustain that output rate, potentially at the expense of greater resource consumption.

Rather than selecting only two optimal configurations, the optimiser would preserve the non-dominated trade-offs between these objectives. These configurations could then be scaled to different production targets, allowing users to compare resource efficiency and infrastructure requirements without repeating the complete graph optimisation.

#### 2. Restore inherent productivity and support productivity research

As outlined in the Current Limitations section, inherent machine productivity has been temporarily disabled because of its impact on the graph optimisation search space. The redesigned algorithm described above should allow these productivity bonuses to be restored without substantially increasing computational complexity.

A further extension will introduce support for productivity research, which provides additional productivity bonuses to specific recipes. These bonuses can significantly change which module configurations are optimal, particularly as recipes approach the 300% productivity cap.

The intended approach is to precompute a set of candidate configurations and adjust their productivity effects for a specified research level, allowing the optimiser to select the appropriate configurations without repeating the full graph search for every level. However, the exact algorithm for efficiently preserving and evaluating configurations across different research levels has yet to be determined.

#### 3. Introduce mining optimisation and scaling

Mining is not currently modelled as an optimisable production stage. However, mining drills support quality, productivity, and speed modules, meaning their configurations affect both the quantity and quality distribution of resources entering an upcycling system.

The optimiser should evaluate mining configurations and incorporate them into systems that consume raw resources. This would include mining productivity research, which differs from recipe productivity research because it is not subject to the same 300% cap.

Practical throughput constraints, such as a mining drill's maximum extraction and output rate, must also be considered.

Including mining would allow systems to be evaluated from initial resource extraction through to their final Legendary outputs, rather than assuming a fixed supply of normal-quality raw materials.

### Code Quality and Performance

#### 1. Automated testing

Introduce a comprehensive automated test suite covering machine and module effects, recipe calculations, graph discovery, material propagation, and optimisation results.

Particular attention should be given to validating Pareto-frontier pruning and ensuring that discarded configurations cannot outperform retained candidates. Smaller, exhaustively enumerable graphs could provide reference solutions against which the optimised search can be tested.

Regression tests would also help ensure that changes to game mechanics and optimisation algorithms do not silently affect existing results.

#### 2. Performance optimisation

Profile the most computationally expensive parts of graph optimisation, particularly candidate generation, state comparisons, and dominance pruning.

Investigate more efficient state representations, caching strategies, and opportunities to reuse computations between systems sharing recipes or intermediate graphs.

The objective is to increase the number and complexity of systems that can be evaluated without sacrificing solution quality.

### User Features and Results Reporting

#### 1. Improved results reporting and resource normalisation

The current results report Legendary output per input craft and per unit time. However, different upcycling systems can require fundamentally different input materials, making direct resource-efficiency comparisons difficult.

Future results should express input requirements using a consistent resource basis, accounting for the production steps required to obtain intermediate materials. This would make it possible to compare otherwise incomparable systems more meaningfully.

Results should also present both efficiency-optimal and throughput-optimal configurations under equivalent input conditions, exposing the differences in Legendary output rates, resource consumption, and machine requirements.

Additional reference configurations, such as maximum-quality and maximum-productivity setups, would help demonstrate the benefits of optimisation over simpler strategies.

#### 2. Static results viewer

Develop a static web interface, hosted using GitHub Pages, for exploring precomputed optimisation results without running the Python optimiser locally.

The intended workflow is for a player to select a target Legendary item and specify a desired production rate, such as 50 Legendary Tungsten Plates per hour. The viewer would evaluate the precomputed candidate configurations, scale their material requirements and processing workloads, and calculate the machine counts required to achieve the target.

Players could then explore trade-offs between material consumption, throughput, and machine requirements, including configurations that become preferable at different production scales.

A secondary workflow could allow players to specify their available input resources and determine the achievable Legendary production rate.

By keeping the computationally expensive optimisation offline, the viewer could provide interactive comparisons using a static site without requiring a server or a Python backend.

### Longer-Term Possibilities

Further extensions could include broader item coverage, support for alternative resource constraints, and more detailed accounting for byproducts and their potential reuse.

These features would build on the revised optimisation algorithm and aim to make the tool useful for designing complete Legendary production systems, rather than only comparing individual upcycling strategies.
