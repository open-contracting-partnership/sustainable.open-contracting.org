---
permalink: /adopcin-de-cps/opciones-de-medicin
title: Opciones de medición
description: "Una vez usted haya podido vincular la política y la acción y luego registrarlo en datos, es posible comenzar a medir la adquisición de CPS. En la mayoría de los casos, la medida que usará es simplemente contar la cantidad de veces que las adquisiciones alcanzan un umbral de CPS acordado."
icon: /assets/images/Icons_Light_Green3.png
notion_id: "65f77799b4194d45bfb637a64aabfcfa"
---
Una vez usted haya podido vincular la política y la acción y luego registrarlo en datos, es posible comenzar a medir la adquisición de CPS. En la mayoría de los casos, la medida que usará es simplemente contar la cantidad de veces que las adquisiciones alcanzan un umbral de CPS acordado.

Estos parámetros podrían ser tan simples como simples etiquetas adjuntas a los avisos que confirman que existe un umbral de CPS y si el documento cumple o no con ese umbral.

```r
PYME apropiada = "Si"
¿Amigable con los negocios de propiedad de mujeres? = "Si"
```

En un programa de hoja de cálculo, puede filtrar los registros que no tienen una característica particular. Para obtener más información sobre cómo hacer esto en Microsoft Excel, puede usar esta guía, asegúrese de verificar la versión de Excel que está usando.

Es importante que estas etiquetas puedan ser validadas. En estos casos, es importante identificar exactamente qué se entiende por PYME (pequeñas y medianas empresas) o empresas dirigidas por mujeres para dar claridad y permitir la coherencia. En el caso de las pequeñas y medianas empresas (PYME), las definiciones podrían girar en torno al número de empleados, la facturación o ambos. En el caso de empresas propiedad de mujeres, las definiciones podrían girar en torno a si la empresa es propiedad de mujeres o si las mujeres constituyen >50% de los beneficiarios finales o >50% de la junta.

Estos parámetros también pueden extenderse a los umbrales establecidos en la política o la ley que hacen que una adquisición esté dentro del alcance de las etiquetas CPS. Por ejemplo, una adquisición dentro del alcance puede ser cualquier adquisición que no contenga municiones o provenga del Ministerio de Defensa y tenga un valor de más de €.25 000

Para aquellos compradores que no tienen acceso a las etiquetas (por ejemplo, datos históricos o falta de una política o legislación que exija la inclusión de cualquier etiqueta), un algoritmo de aprendizaje automático puede identificar la adquisición de CPS en función de la especificación y el identificador de parámetros en la política y la legislación. Con datos claros estructurados en torno a un formato, p. OCDS, un script puede identificar mediante programación el comprador, el proveedor, los umbrales de valor y los patrones dentro del idioma del texto publicado para identificar si un aviso de contratación cumple o no con el umbral CPS.

A partir de estas etiquetas, los datos de adquisiciones se pueden analizar en conjunto, ya sea contando la cantidad de contratos que lograron la definición de CPS:

```r
Nombre del contrato | CPS | 
---------------------
contrato A    | SI |  
contrato B    | SI |  
contrato C    | NO  |

Total contrato = 3
Total CPS = 2
```

O usar esto para entender la proporción de los contratos que cumplen con el estándar:

```r
Porcentaje de contratos con condición CPS
(2/3)*100 = 66.6%
```

En algunos casos, el valor total de los contratos es un indicador útil del compromiso que están asumiendo los compradores con la adquisición de CPS. El siguiente ejemplo muestra cómo calcular el valor total de los contratos CPS.

```r
nombre del contrato | CPS  | valor  | 
----------------------------------
contrato A    | SI    | 100,000 | 
contrato B    | SI    | 120,000 | 
contrato C    | NO     | 160,000 |

Valor total = 100,000 + 120,000 + 160,000 = 380,000
CPS totales = 100,000 + 120,000 = 220,000
```

Puede ser revelador usar valores para establecer una comprensión de la inversión relativa en contratos SPP también:

```r
Porcentaje de contratos con estatus SPP
(220,000/380,000)*100 = 57.9%
```

Las anteriores ecuaciones también se pueden filtrar por categoría, comprador, proveedor, región. Entonces, un analista de SPP de Malasia podría emplear filtros donde el comprador es el Ministerio de Salud de Malasia, la categoría es Medicina, el proveedor Antah Healthcare Group y la región es Penang.

Una buena medida adicional sería publicar claramente los valores de puntuación que forman parte del proceso general de adquisición. Por ejemplo:

```sql
Ponderación de puntuación de compras verdes = 10%
Ponderación del puntaje de desarrollo económico = 2%
Ponderación de puntuación de igualdad de género = NINGUNO
```

Esto permite todo el análisis posible con la primera opción, pero también agrega la posibilidad de añadir mejores correlaciones. En lugar de preguntar si una bandera conduce o no a un resultado correlacionado, es posible analizar si, a medida que aumenta la puntuación de contrataciones CPS, otros factores varían. Los recuentos y las ecuaciones de sumas anteriores se pueden multiplicar por la ponderación para obtener mejores comparaciones entre adquisiciones. A modo de ejemplo, un contrato destinado a una empresa neutra en carbono:

```sql
Para  dos contratos por valor de €100.000

El contrato 1 tiene una puntuación de contratación ecológica del 10 % y tiene un valor de €100 000 
El contrato 2 tiene una puntuación de contratación ecológica del 15 % y un valor de €85 000

El valor de compra verde del Contrato 1 = 100 000*10 % =  €10 000
El valor de compra verde del Contrato 2 = 85 000*15 % = €12 750
```
