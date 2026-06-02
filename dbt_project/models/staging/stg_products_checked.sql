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

    /* Kustuta, kui toitainete väärtused on vigased */
    
    energy_kcal_100g,
    case 
        when invalid_carbohydrates_100g = 1 then null 
        when sugars_greater_than_carbohydrates = 1 then null 
        else carbohydrates_100g 
    end as carbohydrates_100g,
    case 
        when invalid_sugars_100g = 1 then null 
        when sugars_greater_than_carbohydrates = 1 then null
        else sugars_100g 
    end as sugars_100g,
    case 
        when invalid_fat_100g = 1 then null 
        when saturated_fat_greater_than_fat = 1 then null
        else fat_100g 
    end as fat_100g,
    case 
        when invalid_saturated_fat_100g = 1 then null 
        when saturated_fat_greater_than_fat = 1 then null
        else saturated_fat_100g 
    end as saturated_fat_100g,
    case 
        when invalid_proteins_100g = 1 then null 
        else proteins_100g 
    end as proteins_100g,
    case 
        when invalid_salt_100g = 1 then null 
        else salt_100g 
    end as salt_100g,

    /* Kustuta, kui koostisosade nimekiri, pakend või kategooria 
    on vigane */
    case 
        when invalid_ingredients_text = 1 then null 
        else ingredients_text 
    end as ingredients_text,
    case 
        when invalid_packaging = 1 then null 
        else packaging 
    end as packaging,
    case 
        when invalid_quantity = 1 then null 
        else quantity 
    end as quantity

from {{ ref('quality_checks_results') }} as r

/* Eemaldada read, mille tootekood kordub */
where r.product_code_count <= 1


