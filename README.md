# ListenBrainz Docker - Multi-Playlist Sync

🎵 Synchronisation automatique de plusieurs playlists depuis ListenBrainz vers votre bibliothèque musicale locale.

## ✨ Fonctionnalités

- **Multi-playlists** : Crée plusieurs playlists M3U8 automatiquement
- **Synchronisation automatique** : Check périodique des nouvelles recommandations
- **Support complet Deemix** : Téléchargement automatique des tracks
- **Configuration flexible** : JSON pour définir vos playlists
- **Logs détaillés** : Suivi complet du processus

## 🚀 Installation

### 1. Cloner le repository
```bash
git clone https://github.com/YOUR_USERNAME/listenbrainz-docker.git
cd listenbrainz-docker
```

### 2. Configuration
```bash
# Copier le fichier d'exemple
cp docker-compose.override.yml.example docker-compose.override.yml

# Éditer la configuration
nano docker-compose.override.yml
```

### 3. Configurer vos paramètres

Dans `docker-compose.override.yml`, modifiez :

- **`/path/to/your/music`** → Chemin vers votre bibliothèque musicale
- **`YOUR_USERNAME`** → Votre nom d'utilisateur ListenBrainz  
- **`YOUR_ARL_TOKEN_HERE`** → Votre token ARL Deezer

#### 🔑 Obtenir votre ARL Deezer :
1. Allez sur [ce guide](https://rentry.org/firehawk52#deezer-arls)
2. Suivez les instructions pour extraire votre ARL
3. Remplacez `YOUR_ARL_TOKEN_HERE` par votre vraie clé

### 4. Lancer le conteneur
```bash
docker-compose up -d
```

## 📁 Types de playlists supportées

### Recommandations ListenBrainz :
- `weekly-exploration` - Exploration hebdomadaire
- `similar-users` - Basé sur des utilisateurs similaires
- `top-discoveries-of-the-year` - Meilleures découvertes

### Statistiques personnelles :
- `stats/top-tracks?range=this_week` - Top tracks de la semaine
- `stats/top-tracks?range=this_month` - Top tracks du mois
- `stats/top-tracks?range=this_year` - Top tracks de l'année
- `stats/top-tracks?range=all_time` - Top tracks de tous les temps

## ⚙️ Configuration avancée

### Exemple de configuration multi-playlists :
```json
[
  {
    "url": "https://listenbrainz.org/syndication-feed/user/YOUR_USERNAME/recommendations?recommendation_type=weekly-exploration",
    "m3u_filename": "Weekly Exploration.m3u8"
  },
  {
    "url": "https://listenbrainz.org/syndication-feed/user/YOUR_USERNAME/stats/top-tracks?range=this_month&count=50",
    "m3u_filename": "Top Tracks - This Month.m3u8"
  }
]
```

### Variables d'environnement :
- `LOG_LEVEL` : `DEBUG`, `INFO`, `WARNING`, `ERROR`
- `SYNC_INTERVAL` : Intervalle en secondes (défaut: 86400 = 24h)
- `LISTENBRAINZ_BASE_PATH` : Chemin de base pour les fichiers

## 📋 Monitoring

### Voir les logs :
```bash
docker-compose logs -f
```

### Vérifier le statut :
```bash
docker-compose ps
```

### Redémarrer :
```bash
docker-compose restart
```

## 🔒 Sécurité

- ⚠️ **Ne commitez jamais votre `docker-compose.override.yml`** (contient vos clés privées)
- ✅ Le fichier est automatiquement ignoré par Git
- ✅ Utilisez `docker-compose.override.yml.example` comme template

## 🐛 Dépannage

### Token ARL expiré :
1. Récupérez un nouveau token ARL
2. Mettez à jour `DEEMIX_ARL` dans `docker-compose.override.yml`
3. Redémarrez : `docker-compose restart`

### Aucun téléchargement :
1. Vérifiez que votre nom d'utilisateur ListenBrainz est correct
2. Vérifiez que vous avez des recommandations sur ListenBrainz
3. Consultez les logs : `docker-compose logs`

## 🤝 Contribution

1. Fork le projet
2. Créez une branche feature
3. Committez vos changements
4. Push vers la branche
5. Ouvrez une Pull Request

## 📄 Licence

MIT License - voir le fichier LICENSE pour plus de détails.