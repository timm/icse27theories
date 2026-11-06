class State:
    pass

def simulate_brooks(boost_hires, boost_time=10, comm_coef=0.005, train_coef=0.2, prod_rate=5, mature_rate=0.1, ticks=20, vet_start=10):
    u = State()
    u.Vet, u.New, u.Done, u.Todo = vet_start, 0, 0, 500
    
    print(f"--- Scenario: {boost_hires} hires at t={boost_time} | Horizon: {ticks} ticks ---")
    print(f"Params: Vets={vet_start}, comm={comm_coef}, train={train_coef}, prod={prod_rate}, mature={mature_rate}")
    
    for t in range(ticks):
        dt = 1
        v = State()
        
        # Brooks Math
        comm = u.Vet * (u.Vet - 1) / 2 * comm_coef
        train = u.New * train_coef
        prod = u.Vet * (1 - comm - train) * prod_rate
        
        v.Todo = u.Todo - dt * max(0, prod)
        v.Done = u.Done + dt * max(0, prod)v.New = u.New - dt * mature_rate * u.New + (boost_hire
        s if t == boost_time else 0)
        v.Vet = u.Vet + dt * mature_rate * u.New
        
        # Print key milestones to track the curve
        if t == 0 or t == boost_time or t == boost_time + 5 or t == ticks - 1:
            print(f"t={t:02d} | Vets: {u.Vet:.1f} | New: {u.New:.1f} | Net Prod: {prod:.1f} | Done: {u.Done:.1f} | Todo: {u.Todo:.1f}")
            
        u = v
        
    print(f"Final Score (Done - Todo): {u.Done - u.Todo:.1f}\n")

if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "default"
    
    # Original tests
    if mode == "baseline":
        simulate_brooks(boost_hires=0)
    elif mode == "brooks_law":
        simulate_brooks(boost_hires=10)
    elif mode == "break_communication":
        simulate_brooks(boost_hires=10, comm_coef=0.0)
    elif mode == "break_training":
        simulate_brooks(boost_hires=10, train_coef=0.0)
    elif mode == "fast_onboarding":
        simulate_brooks(boost_hires=10, mature_rate=0.5)
    elif mode == "early_hire":
        simulate_brooks(boost_hires=10, boost_time=2)
    elif mode == "massive_surge":
        simulate_brooks(boost_hires=50)
    elif mode == "micro_hire":
        simulate_brooks(boost_hires=1)
    elif mode == "high_productivity":
        simulate_brooks(boost_hires=10, prod_rate=15)
        
    # Phase 3 Stress Tests
    elif mode == "long_horizon":
        simulate_brooks(boost_hires=10, ticks=50)
    elif mode == "small_core_team":
        simulate_brooks(boost_hires=10, vet_start=2)
    elif mode == "steep_learning_curve":
        simulate_brooks(boost_hires=10, mature_rate=0.02, train_coef=0.4)
    elif mode == "last_minute_panic":
        simulate_brooks(boost_hires=10, boost_time=18)
    elif mode == "asynchronous_remote":
        simulate_brooks(boost_hires=10, comm_coef=0.001)