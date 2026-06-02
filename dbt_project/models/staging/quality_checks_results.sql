/* Kvaliteedikontrollide tulemused */

select
    product_code,
    product_name,
    url,
    creator,

    created_datetime,
    last_modified_datetime,
    last_updated_datetime,

    categories_tags,
    categories_en,

    energy_kcal_100g,
    carbohydrates_100g,
    sugars_100g,
    fat_100g,
    saturated_fat_100g,
    proteins_100g,
    salt_100g,

    ingredients_text,
    packaging,
    quantity,
       
    /* Mitu korda iga tootekood esineb? */
    count(*) over (partition by product_code) as product_code_count,

   /* Kas toitained 100 g kohta jäävad vahemikku 0-100? */
    case 
        when carbohydrates_100g < 0 or carbohydrates_100g > 100 then 1
        else 0
    end as invalid_carbohydrates_100g,
    case 
        when sugars_100g < 0 or sugars_100g > 100 then 1
        else 0
    end as invalid_sugars_100g,
    case 
        when fat_100g < 0 or fat_100g > 100 then 1
        else 0
    end as invalid_fat_100g,
    case 
        when saturated_fat_100g < 0 or saturated_fat_100g > 100 then 1
        else 0
    end as invalid_saturated_fat_100g,
    case 
        when proteins_100g < 0 or proteins_100g > 100 then 1
        else 0
    end as invalid_proteins_100g,
    case 
        when salt_100g < 0 or salt_100g > 100 then 1
        else 0
    end as invalid_salt_100g,    

    /* Kas suhkrute sisaldus on suurem kui süsivesikute sisaldus,
     kas küllastunud rasvhapete sisaldus on suurem kui
     rasvade sisaldus? */
    case  when sugars_100g > carbohydrates_100g then 1
        else 0
    end as sugars_greater_than_carbohydrates,

    case  when saturated_fat_100g > fat_100g then 1
        else 0
    end as saturated_fat_greater_than_fat,

    /* Koostiosade nimekiri / pakend / kategooria peaks olema tekst.
    Kas on ainult arv või väga lühike sõne?*/
    case 
        when ingredients_text ~ '^[0-9]+(\.[0-9]+)?$' then 1
        when length(ingredients_text) < 3 then 1
        else 0
    end as invalid_ingredients_text,
    case 
        when packaging ~ '^[0-9]+(\.[0-9]+)?$' then 1
        when length(packaging) < 3 then 1
        else 0
    end as invalid_packaging,
    case 
        when categories_en ~ '^[0-9]+(\.[0-9]+)?$' then 1
        when length(categories_en) < 3 then 1
        else 0
    end as invalid_categories_en,

    /* Kogus peaks olema kas ainult arv või arv koos ühikuga.
    Kas koguse tunnus on midagi muud kui arv / algab arvuga? */
    case 
        when quantity not like '[0-9]%' then 1
        else 0
    end as invalid_quantity

from {{ ref('stg_products') }}

