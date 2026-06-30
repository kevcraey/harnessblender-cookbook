# Dekking van receptorroosters valideren

## User story

Als initiatiefnemer wil ik gewaarschuwd worden als niet alle te beschermen habitats binnen de toetszone zijn gedekt door de IMPACT-depositieberekening, zodat ik weet dat mijn berekening mogelijk onvolledig is.

## Doel of resultaat

Voorkomen dat een PAS-berekening wordt uitgevoerd terwijl niet alle relevante habitats zijn doorgerekend. De gebruiker krijgt een duidelijke waarschuwing als er habitatgebieden zijn die buiten het berekeningsgebied (de receptorroosters) vallen.

- **Probleem**: Als de receptorroosters niet alle relevante habitats dekken, is de PAS-berekening onvolledig.
- **Waarde**: Voorkomt ongeldige berekeningen en geeft de gebruiker de kans om actie te ondernemen.
- **Resultaat**: Gebruiker wordt gewaarschuwd bij onvolledige dekking.

## Context

De toetszone wordt bepaald op basis van de bronlocaties (via PASCAL-3764). Binnen deze toetszone liggen mogelijk te beschermen habitats. De receptorroosters uit IMPACT moeten al deze habitats dekken.

Deze story valideert de **dekking**: vallen alle habitats binnen de receptorroosters?

## Acceptatiecriteria

### [1] Dekking controleren

Given deposities en roosterinformatie zijn geïmporteerd uit IMPACT
And de toetszone is bepaald op basis van de bronlocaties
When de dekking wordt gecontroleerd
Then wordt gecontroleerd of alle te beschermen habitats binnen de toetszone gedekt worden door de receptorroosters

### [2] Foutmelding bij onvolledige dekking

Given een te beschermen habitat ligt (deels) buiten de receptorroosters uit IMPACT
When de gebruiker de PAS-berekening probeert te starten
Then wordt een foutmelding getoond en kan de berekening niet worden gestart

De foutmelding bevat informatie over welke gebieden niet gedekt zijn.
