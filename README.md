# SuperNoisyMario
A modified supermario game based on https://github.com/marblexu/PythonSuperMario.
* Create a new map.
* Three different challenges (you need to solve them with your voice)： 

  1) Turning your tone into a bridge of light, allowing Mario to cross the obstacle to the pipe in the other side. 
  2) Make different tones and change the loudness of your voice to kill the enemies.
  3) Control the pitch through the stars to generate your way forward.

# Requirement
* Python 3.7
* Python-Pygame 1.9
* Pyaudio 0.2.11

# How To Start Game
$ python main.py

# How to Play
* use key "A/D" to control player
* use key 'W' to jump
  
# Note
  1) For the first challenge, you need to keep the sound as smooth as possible. If the frequency bridge you built has severe ups and downs, please rebuild the bridge. Do not try to jump over some steep parts, you may get stuck. Please restart the game when you find that you are stuck.
  2) When you play this game, you need to ensure that the surrounding environment is relatively quiet, otherwise it will cause some trouble, as the game is sensitive to the loudness and frequency of the sound.

# Demo
![challenge_1](https://github.com/clearlove43967/aist2010/blob/master/resources/demo/challenge_1.png)
![challenge_2](https://github.com/clearlove43967/aist2010/blob/master/resources/demo/challenge.png)
![challenge_3](https://github.com/clearlove43967/aist2010/blob/master/resources/demo/challenge_3.png)
