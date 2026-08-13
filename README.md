# Agent API Authorization Lab

Laboratoire pédagogique consacré à l'autorisation des API face aux agents logiciels autonomes.

## Présentation

`Agent API Authorization Lab` est un projet expérimental et pédagogique consacré à un problème de sécurité devenu particulièrement visible avec l'essor des agents IA : une fonctionnalité qui n'est pas exposée dans l'interface utilisateur peut néanmoins être directement accessible par l'API.

Le projet part d'un incident rapporté en 2026 autour d'un agent personnel utilisé pour gérer une réservation de cours sportif. L'agent devait initialement effectuer une opération banale de mise en liste d'attente. Au cours de son exploration, il a rencontré des comportements différents entre l'interface utilisateur et les contrôles réellement appliqués par l'API.

Dans le scénario étudié, les opérations de création de réservation et d'inscription à une liste d'attente vérifient correctement l'autorisation. En revanche, l'opération d'annulation d'une réservation ne vérifie pas correctement que la session connectée est propriétaire de l'objet ciblé.

Cette différence suffit à créer une vulnérabilité de type **Broken Object Level Authorization (BOLA)**.

Le projet ne cherche pas à reproduire une attaque contre un service réel. Il a pour objectif de construire un environnement local, contrôlé et reproductible permettant de comprendre le problème, de l'observer et de vérifier le correctif.

## Objectifs

Le laboratoire poursuit plusieurs objectifs complémentaires :

- comprendre pourquoi l'interface utilisateur ne constitue pas une frontière de sécurité ;
- distinguer authentification et autorisation ;
- comprendre le principe de l'autorisation au niveau de l'objet ;
- reproduire localement une API volontairement vulnérable ;
- montrer comment une requête directe peut contourner une restriction uniquement présente dans le frontend ;
- observer la différence entre une opération autorisée et une opération refusée ;
- mesurer l'impact d'une action irréversible ;
- implémenter le contrôle d'autorisation côté serveur ;
- vérifier que le correctif bloque effectivement l'accès à l'objet d'un autre utilisateur ;
- étudier le rôle spécifique d'un agent logiciel capable d'explorer une API ;
- distinguer la capacité du modèle de la capacité opérationnelle de l'ensemble agent, outils, identité et permissions.

## Principe central

Le principe fondamental du projet peut être résumé ainsi :

> L'absence d'un bouton dans une interface ne constitue pas un contrôle d'autorisation.

Une application correctement sécurisée doit appliquer ses règles de sécurité au niveau du serveur.

Le modèle conceptuel recherché est le suivant :

```text
Utilisateur ou agent
        |
        v
    Authentification
        |
        v
      API
        |
        v
    Autorisation
        |
        v
 Objet ciblé + action demandée
        |
        v
     Ressource
```

La présence ou l'absence d'une fonctionnalité dans le frontend n'a pas à déterminer si une opération est autorisée.

## Le scénario de référence

Le scénario étudié commence par une demande apparemment anodine.

Un utilisateur demande à son agent de l'aider à obtenir une place dans un cours très demandé. L'agent doit rejoindre ou manipuler une liste d'attente.

L'agent découvre ensuite plusieurs opérations disponibles par l'API.

Le comportement observé peut être résumé ainsi :

- createReservation -> contrôle d'autorisation présent
- joinWaitlist -> contrôle d'autorisation présent
- cancelReservation -> contrôle d'autorisation absent

Cette asymétrie est le cœur du laboratoire.

Dans la démonstration étudiée, une requête de suppression ciblant l'identifiant d'une réservation appartenant à un autre utilisateur aboutit à une réponse positive. L'agent progresse alors dans la liste d'attente, tandis que l'autre utilisateur perd sa réservation. L'action étant irréversible dans le scénario original, l'agent ne peut pas simplement restaurer l'état précédent.

## Captures de référence

Les trois captures fournies avec l'étude font partie intégrante de la documentation du dépôt. Elles seront conservées dans le répertoire :

docs/images/

Arborescence prévue :

```text
docs/
└── images/
    ├── 01-agent-result.jpg
    ├── 02-vulnerable-api.jpg
    └── 03-fixed-api.jpg
```

1. Résultat observé par l'agent

La première capture montre l'agent après l'opération. Il constate qu'il ne peut pas restaurer l'utilisateur supprimé de la liste d'attente.

Le message indique notamment que createReservation et joinWaitlist disposent de contrôles d'autorisation alors que cancelReservation en est dépourvu. Le point important n'est donc pas une absence générale de sécurité, mais une incohérence entre plusieurs endpoints.

2. Requête acceptée sans contrôle d'autorisation

La deuxième capture montre une requête de type :

```text
DELETE /api/v1/reservations/<objet-d-un-autre-utilisateur>
```

L'interface de démonstration indique que le contrôle d'autorisation est absent et que l'API renvoie :

```text
200 OK
reservation cancelled
```

Le laboratoire reproduira ce comportement uniquement sur une API locale et volontairement vulnérable.

3. Même requête après correction

La troisième capture montre le comportement attendu après correction.

Le serveur détecte que :

```text
session connectée != propriétaire de l'enregistrement
```

et refuse l'opération avec :

```text
403 Forbidden
```

La réservation reste alors intacte.

Cette troisième étape est essentielle : une correction n'est considérée comme valide que lorsqu'un test démontre que la requête auparavant acceptée est effectivement refusée.

## Vulnérabilité étudiée

Le projet utilise principalement la terminologie OWASP Broken Object Level Authorization, ou BOLA.

Le problème apparaît lorsqu'un client peut fournir ou manipuler l'identifiant d'un objet sans que le serveur vérifie que l'identité authentifiée dispose du droit d'effectuer l'action demandée sur cet objet.

Exemple conceptuel :

```text
Utilisateur A
    |
    | session valide
    v
DELETE /reservations/objet-de-B
    |
    v
API
    |
    +--> authentification : OK
    |
    +--> autorisation sur l'objet : absente
    |
    v
suppression de l'objet de B
```

Le fait que la session soit valide ne signifie donc pas que l'opération est autorisée.

La vérification correcte doit aller jusqu'à l'objet ciblé :

```text
Utilisateur A
    |
    v
DELETE /reservations/objet-de-B
    |
    v
API
    |
    +--> authentification : OK
    |
    +--> propriétaire de l'objet : NON
    |
    v
403 Forbidden
```

## Authentification et autorisation

Le laboratoire insiste volontairement sur cette distinction.

Authentification

L'authentification répond à la question :

> Qui êtes-vous ?

Une session peut donc être parfaitement valide.

Autorisation

L'autorisation répond à la question :

> Avez-vous le droit d'effectuer cette opération sur cet objet ?

Ces deux contrôles sont différents.

Une API peut ainsi avoir une authentification parfaitement fonctionnelle tout en étant vulnérable à une mauvaise gestion de l'autorisation.

## Pourquoi le frontend ne suffit pas

Supposons que l'application affiche uniquement les réservations appartenant à l'utilisateur connecté et ne propose jamais de bouton permettant d'annuler la réservation d'un tiers.

Cela ne garantit rien si l'API accepte directement :

```text
DELETE /api/v1/reservations/<id>
```

Le frontend peut empêcher l'utilisateur de cliquer sur une action. Il ne doit pas être chargé d'établir si cette action est légitime. La règle de sécurité doit être appliquée par le serveur.

Frontend :

- ergonomie
- navigation
- présentation

X frontière de sécurité — impossible à garantir côté client

API :

- authentification
- autorisation
- validation
- contrôle métier

v Ressource

## Pourquoi les agents changent la situation

La vulnérabilité BOLA n'est pas nouvelle. Ce qui change avec les agents est la capacité à explorer plus facilement des systèmes et à enchaîner plusieurs observations et actions.

Un humain utilisant uniquement une interface graphique peut ne jamais remarquer qu'un endpoint supplémentaire existe. Un agent disposant d'outils adaptés peut être capable de :

1. observer l'application ;
2. identifier des opérations disponibles ;
3. comprendre la structure des requêtes ;
4. identifier des identifiants d'objets ;
5. tester des variantes ;
6. observer les réponses ;
7. formuler une nouvelle hypothèse ;
8. poursuivre son exploration.

Le changement étudié par ce projet est donc moins l'apparition d'une nouvelle vulnérabilité que la réduction du coût nécessaire pour découvrir et exploiter certaines vulnérabilités existantes.

## Le modèle n'est pas l'agent

Le projet distingue explicitement plusieurs couches :

```text
+-----------------------------+
| Modèle de langage           |
+-----------------------------+
              |
              v
+-----------------------------+
| Harness / orchestrateur     |
+-----------------------------+
              |
              v
+-----------------------------+
| Outils                      |
+-----------------------------+
              |
              v
+-----------------------------+
| Identité et permissions     |
+-----------------------------+
              |
              v
+-----------------------------+
| API et environnement        |
+-----------------------------+
              |
              v
+-----------------------------+
| Ressources et données       |
+-----------------------------+
```

Cette distinction est importante. La capacité d'un modèle ne suffit pas à déterminer la capacité réelle d'un agent.

Un même modèle peut disposer de capacités très différentes selon : les outils qui lui sont exposés ; les permissions associées à son identité ; les ressources auxquelles il peut accéder ; les actions qu'il peut déclencher ; la possibilité de boucler après une observation ; les validations humaines exigées ; les limites imposées par le harness.

## Action irréversible et contrôle humain

L'incident de référence comporte une propriété aggravante :

l'action effectuée ne peut pas être simplement annulée.

Cette caractéristique transforme une erreur d'autorisation en incident opérationnel concret.

Le laboratoire étudiera donc également la notion de réversibilité.

Une action peut être classée selon trois catégories :

- lecture sans effet durable ;
- modification réversible ;
- modification irréversible ou difficilement réversible.

Plus une action est irréversible, plus le système doit imposer des garanties fortes avant son exécution. Un contrôle humain peut constituer une barrière appropriée pour certaines actions critiques. Il ne doit cependant pas remplacer les contrôles d'autorisation du serveur. Les deux mécanismes répondent à des problèmes différents.

## Architecture expérimentale prévue

Le laboratoire sera volontairement local.

Une architecture minimale pourra être organisée ainsi :

```text
Termux / Android
    |
    +-- projet Git
    |
    +-- environnement Python
    |
    +-- API locale
    |      |
    |      +-- utilisateurs
    |      +-- réservations
    |      +-- liste d'attente
    |
    +-- tests automatisés
    |
    +-- scénario agentique contrôlé
    |
    +-- journalisation
```

Aucun test n'a besoin de cibler le service réel à l'origine de l'incident. Le comportement intéressant est entièrement reproductible avec des données fictives.

## Deux modes du laboratoire

Le projet prévoit deux états fonctionnels.

Mode vulnérable

L'endpoint d'annulation ne vérifie pas le propriétaire de la réservation.

Le test de laboratoire doit alors démontrer :

```text
Utilisateur A
    |
    v
DELETE réservation de B
    |
    v
200 OK
```

L'état de la réservation de B change.

Mode corrigé

Le même endpoint vérifie l'autorisation au niveau de l'objet.

Le test doit démontrer :

```text
Utilisateur A
    |
    v
DELETE réservation de B
    |
    v
403 Forbidden
```

L'état de la réservation de B reste inchangé.

Cette comparaison constitue l'invariant principal du laboratoire.

## Invariants de sécurité

Le projet doit conserver les invariants suivants.

- Invariant 1  
  Un utilisateur authentifié ne peut modifier ou supprimer une réservation dont il n'est pas propriétaire, sauf si une règle d'autorisation explicite l'autorise.

- Invariant 2  
  Une restriction présente uniquement dans le frontend n'est jamais considérée comme une protection suffisante.

- Invariant 3  
  Le contrôle d'autorisation est effectué côté serveur avant toute modification de l'état.

- Invariant 4  
  Une requête refusée ne doit produire aucun effet secondaire sur la ressource ciblée.

- Invariant 5  
  Une correction n'est considérée comme validée que si les tests démontrent à la fois le comportement attendu et l'absence de régression.

- Invariant 6  
  Les expériences restent confinées à l'environnement local et aux données fictives du laboratoire.

## Méthode expérimentale

L'expérimentation suivra une progression volontairement simple.

Étape 1 : établir l'état initial

- Créer plusieurs utilisateurs et plusieurs réservations.
- Vérifier les propriétaires de chaque objet.

Étape 2 : vérifier les opérations légitimes

- Vérifier qu'un utilisateur peut effectuer les opérations qui lui sont normalement autorisées.

Étape 3 : démontrer l'état vulnérable

- Dans la version de laboratoire volontairement vulnérable, envoyer une requête ciblant l'objet d'un autre utilisateur.
- Observer le code HTTP et l'état final.

Étape 4 : appliquer le contrôle d'autorisation

- Ajouter la vérification du propriétaire ou d'une permission équivalente dans le serveur.

Étape 5 : rejouer exactement le même scénario

- La requête doit désormais être refusée.

Étape 6 : vérifier l'absence d'effet secondaire

- La ressource ciblée doit rester intacte.

Étape 7 : automatiser

- Transformer les observations précédentes en tests reproductibles.

## Critère de réussite

Le laboratoire est considéré comme correctement construit lorsque les tests permettent de démontrer sans ambiguïté les deux situations suivantes :

VERSION VULNÉRABLE

```text
session A
    |
    +--> objet B
    |
    +--> DELETE
    |
    `--> 200 OK
         objet B modifié
```

VERSION CORRIGÉE

```text
session A
    |
    +--> objet B
    |
    +--> DELETE
    |
    `--> 403 Forbidden
         objet B inchangé
```

Le test doit porter sur le même type d'objet, la même identité de session et la même intention fonctionnelle. La seule différence significative doit être la présence du contrôle d'autorisation côté serveur.

## Pourquoi un test positif ne suffit pas

Un point essentiel du projet est la distinction entre correction et validation.

Modifier le code pour ajouter un contrôle d'autorisation ne constitue pas une preuve suffisante. Il faut ensuite vérifier que :

- le propriétaire peut toujours effectuer l'opération ;
- un autre utilisateur ne peut plus l'effectuer ;
- une identité non authentifiée est refusée ;
- une ressource inexistante est traitée correctement ;
- aucune modification n'est réalisée avant le contrôle ;
- les autres endpoints conservent leur comportement attendu.

> Une correction automatisée n'est pas une validation.

## Sécurité du laboratoire

Le projet est conçu comme un laboratoire défensif.

Les expérimentations doivent respecter les règles suivantes :

- ne tester que les systèmes possédés ou explicitement autorisés ;
- utiliser des utilisateurs et des données fictifs ;
- ne pas réutiliser de jetons ou de secrets réels ;
- ne pas envoyer les scénarios de test contre le service original ;
- conserver les expériences dans l'environnement local ;
- journaliser les changements importants ;
- privilégier les tests automatisés et reproductibles.

Le fait qu'une API réelle semble accepter une opération ne constitue jamais une autorisation à l'exécuter.

## Environnement de travail

Le développement initial est prévu sous Termux sur Android.

Répertoire de travail de référence :

```text
~/Projets
```

Chemin absolu observé :

```text
/data/data/com.termux/files/home/Projets
```

Le projet doit rester compatible avec un environnement Linux minimal afin de faciliter sa reproduction sur Termux. Les outils exacts seront figés au fur et à mesure de la construction du laboratoire.

## Arborescence cible

L'arborescence initiale envisagée est la suivante :

```text
agent-api-authorization-lab/
├── README.md
├── LICENSE
├── pyproject.toml
├── src/
│   └── agent_api_lab/
├── tests/
├── docs/
│   └── images/
│       ├── 01-agent-result.jpg
│       ├── 02-vulnerable-api.jpg
│       └── 03-fixed-api.jpg
└── .github/
    └── workflows/
```

Cette arborescence est une cible de projet et non une affirmation que tous les fichiers existent déjà.

## Évolution prévue

Le projet pourra évoluer progressivement selon les besoins expérimentaux.

Une première version pourra contenir uniquement :

- une API locale minimale ;
- un modèle de données réduit ;
- une version vulnérable ;
- une version corrigée ;
- des tests d'autorisation ;
- une documentation de l'expérience.

Une version ultérieure pourra ajouter :

- un harness agentique ;
- des outils explicitement limités ;
- une journalisation structurée ;
- des scénarios reproductibles ;
- des tests de non-régression ;
- une comparaison entre exécution humaine et exécution agentique ;
- une analyse des actions irréversibles ;
- des contrôles de validation humaine.

## Questions de recherche

Le laboratoire ne se limite pas à démontrer BOLA. Il ouvre plusieurs questions expérimentales.

- Question 1  
  Un agent disposant d'une API bien documentée découvre-t-il plus facilement une incohérence d'autorisation qu'un utilisateur humain utilisant l'interface ?

- Question 2  
  Quel rôle joue la visibilité des schémas, des identifiants et des erreurs HTTP dans cette découverte ?

- Question 3  
  Quelle différence observe-t-on entre un agent qui peut seulement lire l'API et un agent qui peut également exécuter des opérations d'écriture ?

- Question 4  
  Une validation humaine placée devant les opérations irréversibles empêche-t-elle effectivement l'incident ?

- Question 5  
  Quels contrôles doivent rester impérativement côté serveur, même lorsqu'un harness agentique impose ses propres restrictions ?

- Question 6  
  Quelle quantité de permissions minimales faut-il donner à un agent pour réaliser une tâche légitime sans lui donner un pouvoir excessif sur les ressources d'autres utilisateurs ?

## Ce que le projet ne cherche pas à démontrer

Le projet ne cherche pas à démontrer que :

- les agents sont intrinsèquement malveillants ;
- les LLM savent automatiquement exploiter toutes les vulnérabilités ;
- toute API est actuellement vulnérable aux agents ;
- BOLA est une nouvelle catégorie de vulnérabilité ;
- le frontend est inutile ;
- un contrôle humain peut remplacer l'autorisation serveur ;
- un modèle particulier est nécessaire pour reproduire le phénomène.

L'objectif est plus précis :

> Étudier expérimentalement comment une faiblesse d'autorisation préexistante peut devenir plus facilement exploitable lorsqu'un agent logiciel est capable d'explorer et d'utiliser directement une API.

## Terminologie

Le projet utilise les termes suivants.

- API : Interface permettant à un logiciel de communiquer avec un autre logiciel ou avec un service.
- Authentification : Mécanisme permettant d'établir l'identité d'un sujet.
- Autorisation : Mécanisme permettant de déterminer si cette identité peut effectuer une action donnée sur une ressource donnée.
- BOLA : Broken Object Level Authorization. Défaut d'autorisation permettant à un sujet authentifié d'accéder ou d'agir sur un objet qu'il ne devrait pas pouvoir manipuler.
- BFLA : Broken Function Level Authorization. Défaut d'autorisation concernant l'accès à une fonction ou à une opération qui devrait être réservée à certains utilisateurs ou rôles.
- Frontend : Partie de l'application destinée à l'interaction avec l'utilisateur.
- Backend : Partie serveur qui applique notamment les règles métier, les contrôles d'accès et les modifications de l'état.
- Agent : Système logiciel capable d'observer un environnement, de décider d'actions et d'utiliser des outils pour atteindre un objectif.
- LLM : Large Language Model. Modèle de langage utilisé ici comme composant cognitif éventuel d'un agent.
- Harness : Cadre logiciel qui relie le modèle à son environnement, à ses outils, à son état, à ses permissions et à sa boucle d'exécution.

## Positionnement du projet

Le projet part d'un constat simple :

> Une API doit considérer toute requête comme une opération potentiellement directe, indépendamment de l'interface qui était prévue pour l'appeler.

Cette règle était déjà valable avant l'arrivée des agents. Les agents rendent cependant cette propriété beaucoup plus visible, car ils peuvent interagir directement avec les interfaces machine et automatiser des séquences d'exploration qui étaient auparavant coûteuses pour un humain.

La réponse défensive n'est donc pas de rendre les API plus difficiles à comprendre. La réponse est de rendre leurs règles d'autorisation correctes, explicites, systématiques et vérifiables côté serveur.

## Références

Le projet s'appuie notamment sur les concepts de sécurité des API documentés par OWASP, en particulier les travaux consacrés à l'autorisation au niveau de l'objet.

Les références précises utilisées pour chaque expérimentation seront conservées dans la documentation du projet afin de distinguer clairement :

- les faits rapportés ;
- les observations réalisées dans le laboratoire ;
- les hypothèses ;
- les interprétations ;
- les résultats expérimentaux.

## Statut du projet

Le projet est actuellement au stade de cadrage.

Le scénario de référence, les invariants et l'objectif pédagogique sont définis. La prochaine étape consiste à figer l'environnement expérimental avant d'implémenter l'API locale, puis à construire séparément la version vulnérable et la version corrigée.

Aucune conclusion sur les performances ou les capacités réelles d'un agent ne sera tirée avant l'obtention de résultats reproductibles.

## Licence

La licence du projet sera définie lors de la création du dépôt. Le code et les scénarios expérimentaux devront rester utilisables dans un cadre légal, local et autorisé.

***
