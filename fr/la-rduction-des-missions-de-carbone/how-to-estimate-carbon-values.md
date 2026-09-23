---
permalink: "/la-rduction-des-missions-de-carbone/how-to-estimate-carbon-values"
title: "How to estimate carbon values?"
description: "The most basic way to estimate the carbon value of a contract is to multiply the contract value by a coefficient. One example coefficient is the carbon values derived from categories of goods and services. Spend Network has a table that calculates carbon tonnage based on CPV and UNSPSC. This presents a high level picture of what carbon value is associated with: for instance, a taxi contract. "
icon: "/assets/images/Icons_Light_Green3.png"
notion_id: "0c14bbcbe3a84c2b8dcfa48ced98e465"
---
The most basic way to estimate the carbon value of a contract is to multiply the contract value by a coefficient. One example coefficient is the carbon values derived from categories of goods and services. Spend Network has a table that calculates carbon tonnage based on CPV and UNSPSC. This presents a high level picture of what carbon value is associated with: for instance, a taxi contract. 

<div class="notion-text"></div>

<div class="notion-code no-wrap"><button class="notion-code__copy-button"><svg class="notion-icon notion-icon__copy" viewBox="0 0 14 16"><path d="M2.404 15.322h5.701c1.26 0 1.887-.662 1.887-1.927V12.38h1.154c1.254 0 1.91-.662 1.91-1.928V5.555c0-.774-.158-1.266-.626-1.74L9.512.837C9.066.387 8.545.21 7.865.21H5.463c-1.254 0-1.91.662-1.91 1.928v1.084H2.404c-1.254 0-1.91.668-1.91 1.933v8.239c0 1.265.656 1.927 1.91 1.927zm7.588-6.62c0-.792-.1-1.161-.592-1.665L6.225 3.814c-.452-.462-.844-.58-1.5-.591V2.215c0-.533.28-.832.843-.832h2.38v2.883c0 .726.386 1.113 1.107 1.113h2.83v4.998c0 .539-.276.832-.844.832H9.992V8.701zm-.79-4.29c-.206 0-.288-.088-.288-.287V1.594l2.771 2.818H9.201zM2.503 14.15c-.563 0-.844-.293-.844-.832V5.232c0-.539.281-.837.85-.837h1.91v3.187c0 .85.416 1.26 1.26 1.26h3.14v4.476c0 .54-.28.832-.843.832H2.504zM5.79 7.816c-.24 0-.346-.105-.346-.345V4.547l3.223 3.27H5.791z"></path></svg>Copy</button><pre class="language-sql"><code class="language-sql">Carbon value = Contract value multiplied by Carbon coefficient

Facilities management&#x27;s estimated carbon emissions/$ = 610.69 tonnes CO2/$ million

A $5 million dollar FM contract would therefore yield 3053.44 tonnes of CO2</code></pre><figcaption class="notion-caption notion-semantic-string"></figcaption></div>

<div class="notion-text"></div>

In isolation, this data cannot be analysed: raw contract values gives an incomplete valuation. For instance, a notice for 5 million might be 5 million over 1 year or 5 million over 10. Tracking raw contract values creates uneven and highly skewed data (for instance, a large infrastructure contract awarded one year will skew the entire dataset).

<div class="notion-text"></div>

Therefore, in order to better estimate the carbon value of a contract, it is necessary to calculate the contract value by using the award notice value and the contract start and end date.

<div class="notion-text"></div>

<div class="notion-code no-wrap"><button class="notion-code__copy-button"><svg class="notion-icon notion-icon__copy" viewBox="0 0 14 16"><path d="M2.404 15.322h5.701c1.26 0 1.887-.662 1.887-1.927V12.38h1.154c1.254 0 1.91-.662 1.91-1.928V5.555c0-.774-.158-1.266-.626-1.74L9.512.837C9.066.387 8.545.21 7.865.21H5.463c-1.254 0-1.91.662-1.91 1.928v1.084H2.404c-1.254 0-1.91.668-1.91 1.933v8.239c0 1.265.656 1.927 1.91 1.927zm7.588-6.62c0-.792-.1-1.161-.592-1.665L6.225 3.814c-.452-.462-.844-.58-1.5-.591V2.215c0-.533.28-.832.843-.832h2.38v2.883c0 .726.386 1.113 1.107 1.113h2.83v4.998c0 .539-.276.832-.844.832H9.992V8.701zm-.79-4.29c-.206 0-.288-.088-.288-.287V1.594l2.771 2.818H9.201zM2.503 14.15c-.563 0-.844-.293-.844-.832V5.232c0-.539.281-.837.85-.837h1.91v3.187c0 .85.416 1.26 1.26 1.26h3.14v4.476c0 .54-.28.832-.843.832H2.504zM5.79 7.816c-.24 0-.346-.105-.346-.345V4.547l3.223 3.27H5.791z"></path></svg>Copy</button><pre class="language-sql"><code class="language-sql">Contract value = value divided by (end date minus start date) 

Carbon value = Contract value multiplied by Carbon coefficient

A $5 million dollar FM contract spread over 10 years would yield 305.34 tonnes/year</code></pre><figcaption class="notion-caption notion-semantic-string"></figcaption></div>

<div class="notion-text"></div>
