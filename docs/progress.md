# Edenemisraport

## Mis on valmis

- [x] Docker Compose käivitab kõik teenused
- [x] Andmeid saadakse allikast kätte
- [x] Andmed laaditakse `staging` kihti
- [x] Vähemalt üks transformatsioon toimib
- [x] Vähemalt üks näidikulaud on nähtaval
- [ ] Vähemalt üks andmekvaliteedi test läbib

Valmis on andmete sissevõtt veebist alla laaditud CSV failist, mis kajastab andmebaasi hetkeseisu, ja andmebaasist filtreeritakse välja Eesti kohta käivad read (käsitsi käivitatava koodina). Andmed laaditakse PostgreSQL + pg_duckdb _warehouse_'i, kust dbt kasutab neid _source layer_'ina. dbt mudelid arvutavad kolmest kavandatud mõõdikust kaks, Eestis müüdavate toodete koguarvu ning toodete arvu, millel on andmeaasis olemas peamised pakendiandmed. Näidikulaual kuvatakse joonist toodete koguarvu kohta.

## Järgmised sammud

- Transformatsioonide ja kvaliteedikontrollide täiendamine
- Andmebaasi automaatne uuendamine OpenFoodFacts API deltafailidest
- Näidikulaua täiendamine

## Mis takistab

- Kuna enamik tiimiliikmeid on baastaseme rühmast, on projekti tehniline teostamine väljakutse ja tegevused võtavad palju aega.

## Kontrollpunkt

Käsk, millega saab kontrollida, et töövoog töötab:

```bash
uv run python ingestion/bootstrap/load_bootstrap_snapshot.py
```
Oodatav tulemus: käsk tagastab parquet' failist loetud ridade arvu, luuakse tabel raw.raw_products, millesse kirjutatakse andmed, ja käsk tagastab kirjutatud ridade arvu.
