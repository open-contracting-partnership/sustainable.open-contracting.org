---
permalink: /adopcin-de-cps/cmo-medir-la-aceptacin-de-cps
title: Cómo medir la aceptación de CPS
description: "Claramente, en torno a las métricas de CPS se puede adoptar una visión a largo plazo para vincular los objetivos establecidos por la política y la legislación. Esto puede significar que las etiquetas se cuentan contra el cuerpo de los documentos de contratación y se miden a lo largo del tiempo. Entonces, un ejemplo de contratación CPS podría ser:"
icon: /assets/images/Icons_Light_Green3.png
notion_id: f4df3d85a3c442cf89cd4668b7bf178c
---
Claramente, en torno a las métricas de CPS se puede adoptar una visión a largo plazo para vincular los objetivos establecidos por la política y la legislación. Esto puede significar que las etiquetas se cuentan contra el cuerpo de los documentos de contratación y se miden a lo largo del tiempo. Entonces, un ejemplo de contratación CPS podría ser:

```r
Apto para PYME = "Sí"
¿Amigable con los negocios de propiedad de mujeres? = "Sí"
```

Se puede hacer un análisis del desempeño a lo largo del tiempo sobre los recuentos de contrataciones utilizando el año en que se celebró un contrato para el año de cada contrato.

```r
Año    | Número de CPS | Todas las contrataciones | 
----------------------------------------
2019    | 200       | 600              |    
2020    | 150       | 380              |    
2021    | 450       | 650              |  


Para 2019
Todas las contrataciones = 600
ASPP totales = 200
CPS como porcentaje de todas las contrataciones = 200/600 = 33,3 %

Para 2020-2021
Contrataciones CPS en 2020 = 150
Contrataciones CPS en 2021 = 450
2020-2021 diferencia = 450-150 = 300
```

Esto también se puede utilizar para hacer un seguimiento de los cambios año tras año como un porcentaje:

```r
Para 2020-2021
Contrataciones SPP en 2020 = 150
Contrataciones SPP en 2021 = 450

% cambio de edad 2020 a 2021
Diferencia 2020-2021 dividida por contrataciones SPP 2020
2020-2021 diferencia = 450-150 = 300
% de cambio de edad sobre el año anterior = 300/150 = 200%
```

O sobre los valores del contrato:

```r
Año     | Contratos CPS    | Todas las contrataciones |
        | ($millones)      |  ($millones)      |  
-------------------------------------------------
2019    | 400              | 700               |    
2020    | 200              | 1000              |    
2021    | 350              | 850               |  


Para 2020
Todas las contrataciones = $ 1000m
CPS total = $ 200 millones
CPS como porcentaje de todas las contrataciones = 200/1000 = 20 %

Para 2020-2021
Contrataciones CPS en 2020 = 200
Contrataciones CPS en 2021 = 350
2020-2021 Diferencia = 350-200 = 150

% cambio de edad 2020 a 2021
Diferencia 2020-2021 dividida por contrataciones SPP 2020
% cambio de edad 2020 a 2021 = 150/200 = 75%
```

Usar el valor bruto de los contratos es la opción más simple, pero no siempre la mejor opción. La razón es que estos valores pueden verse sesgados por contratos de alto valor. Por ejemplo, un solo contrato grande como la construcción de infraestructura puede valer miles de millones y aumentar la contratación total del año. En este caso, los valores deben analizarse junto con los números de contratos.

La medición de los objetivos a lo largo del tiempo permite tanto a los compradores como a los responsables políticos conocer mejor el rendimiento real frente a los objetivos establecidos por la política y la legislación. Esto puede dar lugar a pruebas poderosas que demuestren que se está trabajando de forma cuantificable hacia los objetivos políticos y legislativos.

Por ejemplo, recopilar datos sobre CPS como este:

```sql
Número de CPS = Total de todas las CPS realizadas dividido por todas las contrataciones
```

Significa que se pueden crear clasificaciones de organizaciones gubernamentales que muestren los buenos y los malos resultados. Por ejemplo, esta lista es ilustrativa de los 5 mejores para 2021:

```r
Comprador                  | Número de CPS  | Número de CPS  |
                           | (real)         | (objetivo)   |  
-------------------------------------------------------
Ministerio de Salud Pública   | 86%         | 70%        |    
Ministerio de Hacienda        | 82%         | 70%        |    
Ministerio de Educación       | 73%         | 70%        |  
Ministerio de Infraestructura | 63%         | 70%        |  

El de peor desempeño es Ministerio de Infraestructura
Seguimiento del rendimiento contra el objetivo
CPS cuenta como un porcentaje de todas las contrataciones = 63%
Número de CPS objetivo = 70 %
Objetivo contra real = 63-70% = -7% contra objetivo
El Ministerio de Infraestructura tiene un rendimiento inferior al 7%
```

Desde una vista de clasificación de alto nivel, los datos se pueden desglosar aún más en hojas de cálculo y paneles. De la lista ilustrativa anterior, tomando el Ministerio de Infraestructura con el peor desempeño en 63%:

```r
Año    | Recuento SPP*   | Recuento SPP* |
       | (real)          | (objetivo)   |  
-------------------------------------
2019    | 75%          | 70%        |    
2020    | 72%          | 70%        |    
2021    | 63%          | 70%        |  
```

Está claro que el cumplimiento del objetivo no solo ha tenido una tendencia a la baja desde 2019, sino que algo sucedió en 2021 para empujar el desempeño muy por debajo del umbral del 70 %.

A menudo, esto puede deberse a cambios inocuos, como un proceso (nuevo sistema de contratación electrónica) o un cambio de personal y la falta de capacitación y comprensión que a menudo acompaña a esto. El desafío al que se enfrentan muchos compradores y autoridades es que tanto estos cambios inocuos como sus consecuencias inesperadas suelen pasar desapercibidos. Por lo tanto, los buenos datos permiten no solo un mejor rendimiento sino también una mejor gestión.

Independientemente, si un organismo ha llevado a cabo una contratación que debería ser una contratación de SPP y no está etiquetada como tal, entonces el organismo de aplicación puede tomar medidas. Por ejemplo, el Ministerio de Infraestructuras ha autorizado una contratación de logística superior a 25.000 € y no la ha liberado como contratación verde; y no lo han estado haciendo durante alrededor del 14% de sus ofertas. Un algoritmo para detectar esto y alertar al Ministerio significa que pueden revisar sus presentaciones de datos de adquisiciones. Esto puede conducir a una mejora continua entre los que tienen un desempeño bajo y bueno por igual.

Este caso de uso ha sido probado con órganos administrativos. En un ejemplo, un organismo administrativo quería aumentar el cumplimiento de una métrica clave de adquisiciones del 80 % al 90 % al 95 %. Dicho algoritmo alertó a este organismo cuando las adquisiciones dentro del alcance en torno a una métrica de contratación no se publicaron adecuadamente y les permitió informar a los organismos públicos en cuestión para que publicaran mejores datos.+++
