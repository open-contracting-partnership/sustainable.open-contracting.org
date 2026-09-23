---
permalink: "/spp-uptake/options-for-measuring"
title: "Options for measuring "
description: "Once you have been able to link policy and action and then record it in data, it is possible to start to measure SPP procurement. In most cases the measurement you will use is simply counting the number of times procurements are meeting an agreed SPP threshold."
icon: "/assets/images/Icons_Light_Green3.png"
notion_id: "a4d02687108d43bb93134822ee7c2c09"
---
Once you have been able to link policy and action and then record it in data, it is possible to start to measure SPP procurement. In most cases the measurement you will use is simply counting the number of times procurements are meeting an agreed SPP threshold.

These parameters could be as simple as simple tags attached to notices confirming that an SPP threshold is in place and whether or not the document complies with that threshold.

<div class="notion-code no-wrap"><button class="notion-code__copy-button"><svg class="notion-icon notion-icon__copy" viewBox="0 0 14 16"><path d="M2.404 15.322h5.701c1.26 0 1.887-.662 1.887-1.927V12.38h1.154c1.254 0 1.91-.662 1.91-1.928V5.555c0-.774-.158-1.266-.626-1.74L9.512.837C9.066.387 8.545.21 7.865.21H5.463c-1.254 0-1.91.662-1.91 1.928v1.084H2.404c-1.254 0-1.91.668-1.91 1.933v8.239c0 1.265.656 1.927 1.91 1.927zm7.588-6.62c0-.792-.1-1.161-.592-1.665L6.225 3.814c-.452-.462-.844-.58-1.5-.591V2.215c0-.533.28-.832.843-.832h2.38v2.883c0 .726.386 1.113 1.107 1.113h2.83v4.998c0 .539-.276.832-.844.832H9.992V8.701zm-.79-4.29c-.206 0-.288-.088-.288-.287V1.594l2.771 2.818H9.201zM2.503 14.15c-.563 0-.844-.293-.844-.832V5.232c0-.539.281-.837.85-.837h1.91v3.187c0 .85.416 1.26 1.26 1.26h3.14v4.476c0 .54-.28.832-.843.832H2.504zM5.79 7.816c-.24 0-.346-.105-.346-.345V4.547l3.223 3.27H5.791z"></path></svg>Copy</button><pre class="language-r"><code class="language-r">SME suitable = &quot;Yes&quot;
Female owned business friendly? = &quot;Yes&quot;</code></pre><figcaption class="notion-caption notion-semantic-string"></figcaption></div>

In a spreadsheet programme, you can filter out records that don’t have a particular feature. To find out more about how to do this in Microsoft Excel you can use this [guidance](https://support.microsoft.com/en-us/office/filter-data-in-a-range-or-table-01832226-31b5-4568-8806-38c37dcc180e), please make sure to check the version of Excel that you’re using.

It is important that these tags can be validated. In these cases, it is important to identify exactly what is meant by SME (small/medium sized enterprises) or women-led businesses to give clarity and allow consistency. In the case of small and medium enterprises (SMEs), definitions could revolve around number of employees, turnover, or both. In the case of women owned businesses, definitions could revolve around whether the business is women-owned or whether women make up >50% of beneficial owners or >50% of the board.

These parameters can also extend to thresholds set in policy or law that make a procurement in-scope for SPP tags. For instance an in-scope procurement might be any procurement that does not contain ammunition, or comes from the Ministry of Defense and has a value of more than €25,000.

For those buyers who do not have access to tags (e.g. historic data or lack of policy or legislation mandating the inclusion of any tags), a machine learning algorithm can identify SPP procurement based on the specification and the parameters identifier in policy and legislation. With clear data structured around a format, e.g. OCDS, a script can programmatically identify the buyer, supplier, value thresholds and the patterns within the language of the published text to identify whether or not a procurement notice meets the SPP threshold.

From these tags, procurement data can be analyzed in aggregate either by counting the number of contracts that achieved the SPP definition:

<div class="notion-code no-wrap"><button class="notion-code__copy-button"><svg class="notion-icon notion-icon__copy" viewBox="0 0 14 16"><path d="M2.404 15.322h5.701c1.26 0 1.887-.662 1.887-1.927V12.38h1.154c1.254 0 1.91-.662 1.91-1.928V5.555c0-.774-.158-1.266-.626-1.74L9.512.837C9.066.387 8.545.21 7.865.21H5.463c-1.254 0-1.91.662-1.91 1.928v1.084H2.404c-1.254 0-1.91.668-1.91 1.933v8.239c0 1.265.656 1.927 1.91 1.927zm7.588-6.62c0-.792-.1-1.161-.592-1.665L6.225 3.814c-.452-.462-.844-.58-1.5-.591V2.215c0-.533.28-.832.843-.832h2.38v2.883c0 .726.386 1.113 1.107 1.113h2.83v4.998c0 .539-.276.832-.844.832H9.992V8.701zm-.79-4.29c-.206 0-.288-.088-.288-.287V1.594l2.771 2.818H9.201zM2.503 14.15c-.563 0-.844-.293-.844-.832V5.232c0-.539.281-.837.85-.837h1.91v3.187c0 .85.416 1.26 1.26 1.26h3.14v4.476c0 .54-.28.832-.843.832H2.504zM5.79 7.816c-.24 0-.346-.105-.346-.345V4.547l3.223 3.27H5.791z"></path></svg>Copy</button><pre class="language-r"><code class="language-r">contract name | SPP | 
---------------------
contract A    | YES |  
contract B    | YES |  
contract C    | NO  |

Total contracts = 3
Total SPP = 2</code></pre><figcaption class="notion-caption notion-semantic-string"></figcaption></div>

Or using that to establish an understanding of the proportion of contracts that met the standard:

<div class="notion-code no-wrap"><button class="notion-code__copy-button"><svg class="notion-icon notion-icon__copy" viewBox="0 0 14 16"><path d="M2.404 15.322h5.701c1.26 0 1.887-.662 1.887-1.927V12.38h1.154c1.254 0 1.91-.662 1.91-1.928V5.555c0-.774-.158-1.266-.626-1.74L9.512.837C9.066.387 8.545.21 7.865.21H5.463c-1.254 0-1.91.662-1.91 1.928v1.084H2.404c-1.254 0-1.91.668-1.91 1.933v8.239c0 1.265.656 1.927 1.91 1.927zm7.588-6.62c0-.792-.1-1.161-.592-1.665L6.225 3.814c-.452-.462-.844-.58-1.5-.591V2.215c0-.533.28-.832.843-.832h2.38v2.883c0 .726.386 1.113 1.107 1.113h2.83v4.998c0 .539-.276.832-.844.832H9.992V8.701zm-.79-4.29c-.206 0-.288-.088-.288-.287V1.594l2.771 2.818H9.201zM2.503 14.15c-.563 0-.844-.293-.844-.832V5.232c0-.539.281-.837.85-.837h1.91v3.187c0 .85.416 1.26 1.26 1.26h3.14v4.476c0 .54-.28.832-.843.832H2.504zM5.79 7.816c-.24 0-.346-.105-.346-.345V4.547l3.223 3.27H5.791z"></path></svg>Copy</button><pre class="language-r"><code class="language-r">Percentage of contracts with an SPP status
(2/3)*100 = 66.6%</code></pre><figcaption class="notion-caption notion-semantic-string"></figcaption></div>

In some cases the total value of contracts is a useful indicator of the commitment that is being made by buyers towards SPP procurement. The below example shows how to calculate the total value of SPP contracts.

<div class="notion-code no-wrap"><button class="notion-code__copy-button"><svg class="notion-icon notion-icon__copy" viewBox="0 0 14 16"><path d="M2.404 15.322h5.701c1.26 0 1.887-.662 1.887-1.927V12.38h1.154c1.254 0 1.91-.662 1.91-1.928V5.555c0-.774-.158-1.266-.626-1.74L9.512.837C9.066.387 8.545.21 7.865.21H5.463c-1.254 0-1.91.662-1.91 1.928v1.084H2.404c-1.254 0-1.91.668-1.91 1.933v8.239c0 1.265.656 1.927 1.91 1.927zm7.588-6.62c0-.792-.1-1.161-.592-1.665L6.225 3.814c-.452-.462-.844-.58-1.5-.591V2.215c0-.533.28-.832.843-.832h2.38v2.883c0 .726.386 1.113 1.107 1.113h2.83v4.998c0 .539-.276.832-.844.832H9.992V8.701zm-.79-4.29c-.206 0-.288-.088-.288-.287V1.594l2.771 2.818H9.201zM2.503 14.15c-.563 0-.844-.293-.844-.832V5.232c0-.539.281-.837.85-.837h1.91v3.187c0 .85.416 1.26 1.26 1.26h3.14v4.476c0 .54-.28.832-.843.832H2.504zM5.79 7.816c-.24 0-.346-.105-.346-.345V4.547l3.223 3.27H5.791z"></path></svg>Copy</button><pre class="language-r"><code class="language-r">contract name | SPP    | value   | 
----------------------------------
contract A    | YES    | 100,000 | 
contract B    | YES    | 120,000 | 
contract C    | NO     | 160,000 |

Total value = 100,000 + 120,000 + 160,000 = 380,000
Total SPP = 100,000 + 120,000 = 220,000</code></pre><figcaption class="notion-caption notion-semantic-string"></figcaption></div>

Using values to establish an understanding of the relative investment in SPP contracts can also be insightful:

<div class="notion-code no-wrap"><button class="notion-code__copy-button"><svg class="notion-icon notion-icon__copy" viewBox="0 0 14 16"><path d="M2.404 15.322h5.701c1.26 0 1.887-.662 1.887-1.927V12.38h1.154c1.254 0 1.91-.662 1.91-1.928V5.555c0-.774-.158-1.266-.626-1.74L9.512.837C9.066.387 8.545.21 7.865.21H5.463c-1.254 0-1.91.662-1.91 1.928v1.084H2.404c-1.254 0-1.91.668-1.91 1.933v8.239c0 1.265.656 1.927 1.91 1.927zm7.588-6.62c0-.792-.1-1.161-.592-1.665L6.225 3.814c-.452-.462-.844-.58-1.5-.591V2.215c0-.533.28-.832.843-.832h2.38v2.883c0 .726.386 1.113 1.107 1.113h2.83v4.998c0 .539-.276.832-.844.832H9.992V8.701zm-.79-4.29c-.206 0-.288-.088-.288-.287V1.594l2.771 2.818H9.201zM2.503 14.15c-.563 0-.844-.293-.844-.832V5.232c0-.539.281-.837.85-.837h1.91v3.187c0 .85.416 1.26 1.26 1.26h3.14v4.476c0 .54-.28.832-.843.832H2.504zM5.79 7.816c-.24 0-.346-.105-.346-.345V4.547l3.223 3.27H5.791z"></path></svg>Copy</button><pre class="language-r"><code class="language-r">Percentage of contracts with an SPP status
(220,000/380,000)*100 = 57.9%</code></pre><figcaption class="notion-caption notion-semantic-string"></figcaption></div>

These above equations can also be filtered by category, buyer, supplier, region. So a Malaysian SPP analyst might employ filters where the buyer is the Ministry of Health of Malaysia, the category is Medicine, the supplier Antah Healthcare Group and the region is Penang.

A good additional measure would be to clearly publish scoring values that form part of the overall procurement process. For instance:

<div class="notion-code no-wrap"><button class="notion-code__copy-button"><svg class="notion-icon notion-icon__copy" viewBox="0 0 14 16"><path d="M2.404 15.322h5.701c1.26 0 1.887-.662 1.887-1.927V12.38h1.154c1.254 0 1.91-.662 1.91-1.928V5.555c0-.774-.158-1.266-.626-1.74L9.512.837C9.066.387 8.545.21 7.865.21H5.463c-1.254 0-1.91.662-1.91 1.928v1.084H2.404c-1.254 0-1.91.668-1.91 1.933v8.239c0 1.265.656 1.927 1.91 1.927zm7.588-6.62c0-.792-.1-1.161-.592-1.665L6.225 3.814c-.452-.462-.844-.58-1.5-.591V2.215c0-.533.28-.832.843-.832h2.38v2.883c0 .726.386 1.113 1.107 1.113h2.83v4.998c0 .539-.276.832-.844.832H9.992V8.701zm-.79-4.29c-.206 0-.288-.088-.288-.287V1.594l2.771 2.818H9.201zM2.503 14.15c-.563 0-.844-.293-.844-.832V5.232c0-.539.281-.837.85-.837h1.91v3.187c0 .85.416 1.26 1.26 1.26h3.14v4.476c0 .54-.28.832-.843.832H2.504zM5.79 7.816c-.24 0-.346-.105-.346-.345V4.547l3.223 3.27H5.791z"></path></svg>Copy</button><pre class="language-sql"><code class="language-sql">Green procurement score weighting = 10%
Economic development score weighting = 2%
Gender equality score weighting = NULL</code></pre><figcaption class="notion-caption notion-semantic-string"></figcaption></div>

This allows all the analysis possible with the first option but also adds the possibility of adding better correlations. Instead of asking whether or not a flag leads to a correlated outcome, it is possible to analyze whether, as SPP procurement score increases, other factors vary. The counts and the sum equations above can thus be multiplied by the weighting to get better comparisons between procurements. By way of example, a contract going to a carbon-neutral business:

<div class="notion-code no-wrap"><button class="notion-code__copy-button"><svg class="notion-icon notion-icon__copy" viewBox="0 0 14 16"><path d="M2.404 15.322h5.701c1.26 0 1.887-.662 1.887-1.927V12.38h1.154c1.254 0 1.91-.662 1.91-1.928V5.555c0-.774-.158-1.266-.626-1.74L9.512.837C9.066.387 8.545.21 7.865.21H5.463c-1.254 0-1.91.662-1.91 1.928v1.084H2.404c-1.254 0-1.91.668-1.91 1.933v8.239c0 1.265.656 1.927 1.91 1.927zm7.588-6.62c0-.792-.1-1.161-.592-1.665L6.225 3.814c-.452-.462-.844-.58-1.5-.591V2.215c0-.533.28-.832.843-.832h2.38v2.883c0 .726.386 1.113 1.107 1.113h2.83v4.998c0 .539-.276.832-.844.832H9.992V8.701zm-.79-4.29c-.206 0-.288-.088-.288-.287V1.594l2.771 2.818H9.201zM2.503 14.15c-.563 0-.844-.293-.844-.832V5.232c0-.539.281-.837.85-.837h1.91v3.187c0 .85.416 1.26 1.26 1.26h3.14v4.476c0 .54-.28.832-.843.832H2.504zM5.79 7.816c-.24 0-.346-.105-.346-.345V4.547l3.223 3.27H5.791z"></path></svg>Copy</button><pre class="language-sql"><code class="language-sql">For two contracts worth €100,000 

Contract 1 has a green procurement score of 10% and worth €100,000
Contract 2 has a green procurement score of 15% and worth €85,000

The green procurement value of Contract 1 = 100,000*10% = €10,000
The green procurement value of Contract 2 = 85,000*15% = €12,750</code></pre><figcaption class="notion-caption notion-semantic-string"></figcaption></div>
