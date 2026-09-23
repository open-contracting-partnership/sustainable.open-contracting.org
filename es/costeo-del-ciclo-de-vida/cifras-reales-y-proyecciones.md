---
permalink: /costeo-del-ciclo-de-vida/cifras-reales-y-proyecciones
title: Cifras reales y proyecciones
description: "We have just looked at the role of estimates in determining a life cycle cost, now we are going to look at the role of actuals, in other words the actual payments that are being made and how they can be used to establish a life cycle cost."
icon: /assets/images/Icons_Light_Green3.png
notion_id: c4d056e74d4540858601070b9d7f1222
---
We have just looked at the role of estimates in determining a life cycle cost, now we are going to look at the role of actuals, in other words the actual payments that are being made and how they can be used to establish a life cycle cost.

Here the challenge is to link the data in an invoice or its payment back to an asset. This can be simple or complex depending on the nature of the asset. A payment to provide facilities management services for a building will be easy to determine, as an invoice will likely include a set of fees that relate to that building. Determining the actual cost of the building is, in this scenario, relatively simple.

```r
Initial build cost = €6,000,000
Month one facilities cost = €600,000
Month two facilities cost = €600,000
Month three facilities cost = €600,000
Month four facilities cost = €600,000
Month five facilities cost = €600,000
Month six facilities cost = €600,000

Total cost = €9,600,000
```

Even if the monthly costs vary it is easy to establish a life cycle cost for this asset. With just six months it is possible to make a useful projection that this asset would cost €78,000,000 over ten years.

When looking at multiple costs associated with multiple assets we have to work a bit harder to get to a lifecycle cost for each asset. If you are maintaining a suite of laptops you will have a variety of costs and these will have to average out to establish a single cost per unit.

```r
One off cost
Original purchase cost = €1,000
Set up fee = €300
Disposal = €500

Annual costs
Licenses = €200 per year
Servicing = €100 per year
Network = €100 per year

Total five year life cycle costs = €1,800 + (€400 * 5) = €3,800
```

This is a relatively simple per unit cost, but you may also need to consider replacement parts,  replacement products, training and support for the laptops as well. In this scenario you can model these extra costs in the following way:

<div class="notion-code no-wrap"><button class="notion-code__copy-button"><svg class="notion-icon notion-icon__copy" viewBox="0 0 14 16"><path d="M2.404 15.322h5.701c1.26 0 1.887-.662 1.887-1.927V12.38h1.154c1.254 0 1.91-.662 1.91-1.928V5.555c0-.774-.158-1.266-.626-1.74L9.512.837C9.066.387 8.545.21 7.865.21H5.463c-1.254 0-1.91.662-1.91 1.928v1.084H2.404c-1.254 0-1.91.668-1.91 1.933v8.239c0 1.265.656 1.927 1.91 1.927zm7.588-6.62c0-.792-.1-1.161-.592-1.665L6.225 3.814c-.452-.462-.844-.58-1.5-.591V2.215c0-.533.28-.832.843-.832h2.38v2.883c0 .726.386 1.113 1.107 1.113h2.83v4.998c0 .539-.276.832-.844.832H9.992V8.701zm-.79-4.29c-.206 0-.288-.088-.288-.287V1.594l2.771 2.818H9.201zM2.503 14.15c-.563 0-.844-.293-.844-.832V5.232c0-.539.281-.837.85-.837h1.91v3.187c0 .85.416 1.26 1.26 1.26h3.14v4.476c0 .54-.28.832-.843.832H2.504zM5.79 7.816c-.24 0-.346-.105-.346-.345V4.547l3.223 3.27H5.791z"></path></svg>Copy</button><template id="B:0"></template><figcaption class="notion-caption notion-semantic-string"></figcaption></div>

Having modeled up the costs associated with replacements and support services to help the laptops function, you can combine these costs into an accurate annual cost before projecting the costs to a full lifecycle cost:

```r
One off cost
Original purchase cost = €1,000
Set up fee = €300
Disposal = €500

Annual costs
Licenses = €200 per year
Servicing = €100 per year
Network = €100 per year
Training & support = €1,600 per year
Replacements = €140 per year

Total annual costs = €200 + €100 + €1,600 + €140 = €2,040

Total five year life cycle costs = €1,800 + (€2,040 * 5) = €12,000
```

We’ve taken the initial cost of a laptop at €1,000 and determined that the actual cost of owning and maintaining these laptops will be closer to €12,000 per laptop. This is a useful insight for buyers, because it clarifies that the primary cost of running the laptops is the €1,600 per year spent on support and training. 

A second laptop that has a better user interface and requires less overall support may well represent better value for money, despite having a much higher unit cost. In the following scenario a laptop costing twice the unit cost but half the support provides a lifecycle cost of €9,000 per unit and a 33% saving on the cheaper unit.

```r
One off cost
Original purchase cost = €2,000
Set up fee = €300
Disposal = €500

Annual costs
Licenses = €200 per year
Servicing = €100 per year
Network = €100 per year
Training & support = €800 per year
Replacements = €140 per year

Total annual costs = €200 + €100 + €800 + €140 = €1,240

Total five year life cycle costs = €2,800 + (€1,240 * 5) = €9,000
```

In this scenario we are combining actual data on the value of an asset, using sampled data on replacements and projected support costs to determine the lifecycle cost of a single asset. We’re also showing how life cycle costing to show that unit costs may not be the best indicator of true value and that meaningful research is required to show where value for money savings can be made.
