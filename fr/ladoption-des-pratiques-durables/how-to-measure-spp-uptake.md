---
permalink: /ladoption-des-pratiques-durables/how-to-measure-spp-uptake
title: How to measure SPP uptake
description: "With clarity around SPP metrics, a long term view can be adopted to tie into targets set by policy and legislation. This can mean that tags are counted against the body of procurement documents and measured over time. So an example SPP procurement might be:"
icon: /assets/images/Icons_Light_Green3.svg
notion_id: "2c87f21c1682422e9c9496635fd12e2b"
---
With clarity around SPP metrics, a long term view can be adopted to tie into targets set by policy and legislation. This can mean that tags are counted against the body of procurement documents and measured over time. So an example SPP procurement might be:

```r
SME suitable = "Yes"
Female owned business friendly? = "Yes"
```

An analysis of performance over time can be undertaken on procurement counts, using the year that a contract was entered into for the year of each contract.

```r
Year    | SPP count | All procurements |   
----------------------------------------
2019    | 200       | 600              |    
2020    | 150       | 380              |    
2021    | 450       | 650              |  


For 2019
All procurements = 600
Total SPP = 200
SPP as a percentage of all procurements = 200/600 = 33.3%

For 2020-2021
SPP procurements in 2020 = 150
SPP procurements in 2021 = 450
2020-2021 difference = 450-150 = 300
```

This can also be used to track Year on Year changes as a percentage:

```r
For 2020-2021
SPP procurements in 2020 = 150
SPP procurements in 2021 = 450


%age change 2020 to 2021
2020-2021 difference divided by 2020 SPP procurements
2020-2021 difference = 450-150 = 300
%age change over the previous year = 300/150 = 200%
```

Or on contract values:

```r
Year    | SPP contracts let | All procurements  |
        | ($millions)       |  ($millions)      |  
-------------------------------------------------
2019    | 400               | 700               |    
2020    | 200               | 1000              |    
2021    | 350               | 850               |  


For 2020
All procurements = $1000m
Total SPP = $200m
SPP as a percentage of all procurements = 200/1000 = 20%

For 2020-2021
SPP procurements in 2020 = 200
SPP procurements in 2021 = 350
2020-2021 Difference = 350-200 = 150

%age change 2020 to 2021
2020-2021 difference divided by 2020 SPP procurements
%age change 2020 to 2021 = 150/200 = 75%
```

Using raw contract values is the simplest option but not always the best option. The reason is, these values can be skewed by high value contracts. For instance, a single large contract like infrastructure building can be worth billions and uplift the entire procurement for the year. In this instance, the values need to be looked at alongside the contract counts.

The measurement of targets over time, allows buyers and policymakers alike to better know actual performance versus targets set by policy and legislation. This can lead to powerful evidence showing that work towards policy and legislative objectives is quantifiably being done.

For instance collecting data on SPPs such as this:

```sql
SPP Count = Total of all SPPs carried out divided by All procurements
```

Means that rankings of government organizations can be created, showing good performers and poor performers. For example this illustrative top 5 list for 2021:

```r
Buyer                      | SPP count   | SPP count  |
                           | (actual)    | (target)   |  
-------------------------------------------------------
Ministry of Public Health  | 86%         | 70%        |    
Ministry of Finance        | 82%         | 70%        |    
Ministry of Education      | 73%         | 70%        |  
Ministry of Infrastructure | 63%         | 70%        |  

The lowest performer is Ministry of Infrastructure
Tracking performance against target
SPP count as a %age of all procurement = 63%
Target SPP count = 70%
Target against actual = 63-70% = -7% against target
Ministry of Infrastructure is underperforming by 7%
```

From a high level ranking view, data can be further broken down on spreadsheets and dashboards. From the above illustrative list, taking the poorest performing Ministry of Infrastructure at 63%:

```r
Year    | SPP count*   | SPP count* |
        | (actual)     | (target)   |  
-------------------------------------
2019    | 75%          | 70%        |    
2020    | 72%          | 70%        |    
2021    | 63%          | 70%        |  
```

It is clear that compliance against the target has not only been on a downward trend since 2019 but something happened in 2021 to push the performance far below the 70% threshold.

This can often be down to innocuous changes such as a process (new e-procurement system) or personnel change and a lack of training and understanding that often accompanies this. The challenge many buyers and authorities face is that both these innocuous changes and their unexpected consequences often go unnoticed. Good data therefore allows not only better performance but better management.

Regardless, if a body has led a procurement that should be an SPP procurement and is not labeled as such, then the enforcement body can take action. For instance, the Ministry of Infrastructure has let a procurement for logistics over €25,000 and has not released it as a green procurement; and they have not been doing so for about 14% of their tenders. An algorithm to pick this up and alert the Ministry means that they can review their procurement data submissions. This can lead to continuous improvement among poor and good performers alike.

This use case has been proven with administrative bodies. In one example, an administrative body wanted to raise compliance on a key procurement metric from 80% to 90% to 95%. Such an algorithm alerted this body when in-scope procurements around a procurement metric were not being adequately published and allowed them to inform the public bodies in question to publish better data.
