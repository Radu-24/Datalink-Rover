import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.monitor import Monitor # <--- Tracks success rate
from stable_baselines3.common.env_util import make_vec_env
from core.environment import RoverEnv
import os
import glob
import re

if __name__ == '__main__':
    # 1. SETUP
    models_dir = "models/PPO"
    log_dir = "logs"
    if not os.path.exists(models_dir): os.makedirs(models_dir)
    if not os.path.exists(log_dir): os.makedirs(log_dir)

    # 2. HARDWARE: 8 Instances for Core Ultra 7
    NUM_ENVS = 8 
    
    # Wrap env in Monitor to enable "rollout/success_rate" logging
    def make_env():
        return Monitor(RoverEnv())

    env = make_vec_env(make_env, n_envs=NUM_ENVS, vec_env_cls=SubprocVecEnv)

    # 3. AUTO-RESUME LOGIC
    files = glob.glob(f"{models_dir}/ppo_rover_*.zip")
    latest_file = None
    steps_done = 0

    if files:
        def get_step(name):
            m = re.search(r"ppo_rover_(\d+).zip", name)
            return int(m.group(1)) if m else 0
        latest_file = max(files, key=get_step)
        steps_done = get_step(latest_file)

    # 4. INITIALIZE
    if latest_file:
        print(f"RESUMING: {latest_file} (Steps: {steps_done})")
        model = PPO.load(latest_file, env=env, device="cpu")
    else:
        print("STARTING FRESH (Monitoring Enabled, Random Spawn)")
        model = PPO(
            "MlpPolicy", 
            env, 
            verbose=1, 
            tensorboard_log=log_dir,
            learning_rate=0.0003,
            n_steps=2048 // NUM_ENVS, 
            batch_size=64,
            gamma=0.99,
            ent_coef=0.01,
            device="cpu" 
        )

    # 5. TRAIN LOOP
    CHECKPOINT = 100000 
    TOTAL_ROUNDS = 100 
    
    start_round = (steps_done // CHECKPOINT) + 1
    
    for i in range(start_round, TOTAL_ROUNDS + 1):
        model.learn(total_timesteps=CHECKPOINT, reset_num_timesteps=False)
        
        current = i * CHECKPOINT
        path = f"{models_dir}/ppo_rover_{current}"
        model.save(path)
        print(f"--- SAVED: {path} ---")

    env.close()