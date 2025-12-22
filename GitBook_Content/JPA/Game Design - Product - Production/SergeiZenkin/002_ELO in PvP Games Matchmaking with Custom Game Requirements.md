---
title: "ELO in PvP Games Matchmaking with Custom Game Requirements"
---

# ELO in PvP Games: Matchmaking with Custom Game Requirements

###### In the past, I’ve often seen PvP projects developed by teams that typically use ELO as their primary matchmaking solution.📝 This always seemed a bit as a risky choice because ELO is certainly a great system, but it was created for other purposes.

🌟First of all, good things about it (in games):  
— It can work and cover a couple of MM basic requirements  
— For games with 1vs1 PvP, with some custom adjustments, ELO can work really good  
  
But in my opinion, when MM systems are going through the design & development phases, it should be built based on detailed requirements from the game perspective. Otherwise, it may be hard to adapt games and ELO to each other, to make it work really well.   
  
🔖What else is important to consider when there is a task to make ELO-based MM (or similar system):  
— If the game is about a bigger format than 1vs1, it should be handled in some way by additional logic (e.g. based on weighted averages).  
— Some calibration mechanics can be useful. Because some players can be very good from the start or learn to be that way very fast.  
— Rating “degradation” through inactivity time could be handy. Some players may leave the game with a high rating and return to it when they forget how to play at the same level.  
— Some kind of “Seasons” with rating downscaling at the start (in a proportional way) may be useful.  
— Custom rules for onboarding of new players. For example, the average rating gain at the start could be higher than zero. It will help to differentiate layers with players of different skill levels.  
— If the game is based not only on the skill but on the power progression as well, it also should be handled (e.g. in the form of the gear score, affecting the ELO rating in direct or indirect form).  
  
⚒️At the end of design, it is helpful to ask yourself: is the final system transparent and flexible enough? Is it easy to operate? After reflection on these questions, some simplification needs could appear in your head. Some other rating systems may be taken into consideration.

![](https://www.gamigion.com/wp-content/uploads/2024/09/Sergei-100x100.jpeg)

About the author

#### [Sergei Zenkin](https://www.gamigion.com/author/sergeizenkin/)

Making games since 2006: started from mods and indie-projects. Mostly Hardcore Genres such as Shooters and Strategy.

[More posts](https://www.gamigion.com/author/sergeizenkin/)