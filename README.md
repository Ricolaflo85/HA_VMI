# HA_VMI
VMI Purevent HA

## Installation du custom component `enocean_gpio`

1. Copier le dossier `custom_components/enocean_gpio` dans le répertoire `config/custom_components` de Home Assistant.
   - Si le dossier `custom_components` n'existe pas, le créer.
2. Vérifier que le fichier `manifest.json` est présent dans `config/custom_components/enocean_gpio`.
3. Installer la dépendance `pyserial` si elle n'est pas déjà présente dans l'environnement Python de Home Assistant.
   - Dans un environnement Home Assistant supervisé, cela peut se faire via un `requirements.txt` ou en installant le package dans l'environnement.

## Configuration dans Home Assistant

Ajouter dans `configuration.yaml` :

```yaml
enocean_gpio:
  port: /dev/ttyS2
```

- `port` est le port série où le module EnOcean est branché.
- Par défaut, le composant utilise `/dev/ttyS2`.

## Utilisation

1. Redémarrer Home Assistant après avoir ajouté la configuration.
2. Le composant lit les trames EnOcean et crée des entités automatiques selon les profils supportés :
   - `d1079 00 00` : Ventilairsec Assistant
   - `d1079 01 00` : VMI Ventilairsec
   - `d106d 00 00` : Capteur IAQ
   - `a5 09 04` : CO2 Sensor
   - `a5 04 01` : Temperature Humidite Sensor
   - `d2 01 12` : Bypass Switch
   - `d5 00 01` : Door contact
3. Les entités sont créées dynamiquement à partir des données reçues.
4. Une fois créées, les entités sont visibles dans le tableau de bord et peuvent être historisées si le `recorder` de Home Assistant est activé.

## Notes

- Le composant ne gère pas de stockage propre : les données sont exposées via les entités Home Assistant.
- Si Home Assistant n'est pas encore capable de lire le port, vérifier les permissions sur le périphérique série et l'accès de l'utilisateur exécutant Home Assistant.
- Les données sont mises à jour à chaque réception d'un telegramme EnOcean valide.
