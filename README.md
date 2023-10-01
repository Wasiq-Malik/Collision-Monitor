# Collision Monitor System for iw.hub

## Table of Contents
1. [Introduction](#introduction)
2. [Implementation Details](#implementation-details)
3. [Solution Proposed](#solution-proposed)
4. [Testing and Validation](#testing-and-validation)
5. [Scalability Considerations](#scalability-considerations)
6. [Theoretical Discussions](#theoretical-discussions)
7. [Conclusion](#conclusion)

## Introduction
Brief overview of the project, its objectives, and expected outcomes.

## Quick Start

### Prerequisites
- Docker installed. [Get Docker](https://docs.docker.com/get-docker/).
- Python 3.9 installed for running unit tests.

### Running the Simulation
1. Open a terminal.
2. Navigate to the project's root directory.
3. Execute: `docker-compose up`

### Viewing the Logs
- To view logs from all running containers, execute: `docker-compose logs`
- To view logs from a specific service, execute: `docker-compose logs <service_name>`

### Stopping the Simulation
1. Press Ctrl+C in the terminal where the simulation is running.
2. To remove the containers, networks, and volumes, execute: `docker-compose down`
### Running the Unit Tests
1. Navigate to the project's root directory in your terminal.
2. Execute: `python -m unittest discover tests`



## Implementation Details
### Technology Stack
- Python
- Docker
- RabbitMQ


### Directory Structure
```
Collision-Monitor/
├── collision_monitor/          # Collision Monitor Service
│   ├── __init__.py
│   ├── collision_monitor.py    # Main logic for Collision Monitor
│   └── Dockerfile
├── robot_simulator/            # Robot Simulator Service
│   ├── __init__.py
│   ├── robot.py                # Main logic for Robot Simulator
│   ├── robot_simulator.py      # Runner script for Robot Simulator
│   ├── Dockerfile
│   └── robot_states/           # Contains initial states of robots
│       ├── robot1.json
│       ├── robot2.json
│       └── robot3.json
├── rabbitmq_client/            # RabbitMQ Client Module
│   ├── __init__.py
│   └── rabbitmq_client.py      # Client logic for RabbitMQ
├── tests/                      # Unit Tests
│   ├── __init__.py
│   ├── test_collision_monitor.py
│   └── test_robot_simulator.py
├── docker-compose.yml          # docker-compose file to orchestrate the simulation
└── wait-for-it.sh              # Script to manage service dependencies in compose
```

## Robot Simulator
### Design and Implementation
Detailing the design choices and implementation details of the robot simulator, including how robots are moving, sending states, and handling commands.

### Initial States and Path
Description of how initial states and paths are defined and loaded for each robot.

## Collision Monitor
### Design Considerations
The Collision Monitor is a micro-service that can be deployed as a standalone container that maintains the global state of all the robots.

#### Global State

In our current implemented simulation we are dealing with only 3 robots, we can simply maintain the global state of our robots in-memory in our collision monitor container. At a larger scale, we will need to sync the global state between each collision monitor container, there we can use redis as a distributed sync. We will discuss large scale again in a later section.

Now that we have the global state sorted out, we need to update the state of each robot upon recieving messages from the rabbitMQ queue. We can simply update the global state dictionary in this case.

#### Reactivity vs. Periodicity

Next, we need to figure out when should we run the collision detection algorithm? should we run it upon recieving each state update? or run it in a background thread at 1 Hz frequency similar to how the robots move? Let's evaluate.

- Reactive Approach (on each state update):
    - Pros:
        - Immediate response to changes in robot states.
        - Potentially more accurate as it uses the most up-to-date information.
        - Easier to implement, no need to manage python threading.
    - Cons:
        - Could be less efficient, especially if state updates are frequent and the collision detection algorithm is complex.
        - Might lead to more frequent command changes, potentially causing instability in robot movements.
- Periodic Approach (at fixed intervals):
    - Pros:
        - More efficient, especially if state updates are frequent.
        - Could lead to more stable and consistent decisions as it considers the states of all robots at the same time.
    - Cons:
        - Less reactive, potential delay in responding to changes in robot states.
        - Might miss some transient states that could be important for collision avoidance.
        - Requires implementing threading.

We opt for the **reactive approach** as we are only dealing with a small number of robots in our simulation and our collision detection can run fast enough (within 1s) to send the required commands to the robots. It is also easy to implement in a short amount of time.

At a large scale, we can opt for a periodic approach where the monitor evaluates the global states with 100s of robots using an efficient collision resolution algorithm and send out the respective pause/resume commands. This solution would be more complex to implement and would require more time.

### Detection Algorithms
We evalute 3 different solutions to detecting collisions between our robots for our simulation. Let's discuss and evaluate each approach.

#### Proximity-Based Approach
- Description: For each pair of robots, calculate the distance between their current positions and predict if they will come within a certain proximity in the next steps.
- Pros: Simple and easy to implement; does not require complex geometric calculations.
- Cons: May not be very accurate; may lead to unnecessary pauses or missed collisions.

#### Path-Based Approach
- Description: For each pair of robots, check if their future paths will intersect and if they will be at the intersection point at the same time.
- Pros: More accurate than the proximity-based approach; can detect collisions before they happen.
- Cons: Requires more complex calculations; may be less efficient for long paths.

#### Grid-Based Approach
- Description: Divide the workspace into a grid and represent the position and path of each robot on the grid. Check for collisions on the grid.
- Pros: Can be efficient and accurate; suitable for environments with many obstacles.
- Cons: Requires discretization of the workspace and paths; may be complex to implement.

Given the time constraints and wanting to reduce the complexity of our solution, we opt for the **Proximity-Based** Solution. It can be a good compromise between simplicity and accuracy for a small number of robots in a simple environment. If more accuracy is needed, we can consider refining the approach or switching to a more accurate but complex approach like path-based future collision detection.

#### Proximity Function

For each pair of robots, calculate the Euclidean distance between their current positions. This will have a runtime of O(n^2). We can improve this algorithm for larger scales by utilising sorting and divide and conquer algorithms which will efficiently calculate the distances between all possibly colliding robots.

The threshold can be the sum of the radii of the equivalent circles of the two robots, where the radius is half of the diagonal of the robot.


The diagonal \(d\) of the robot can be calculated using the Pythagorean theorem:
\[d = √(w² + l²)\]
where \(w\) is the width of the robot and \(l\) is the length of the robot.


The threshold \(T\) for collision can be calculated as:
\[T = (d₁ / 2) + (d₂ / 2)\]
where:
- \(d₁\) and \(d₂\) are the diagonals of the two robots.

As all of our robots are of the same size 6.3 x 14.3 (in Cartesian units), we can simplify our threshold to be the length of the diagonal of the robot.

```python
# Get the positions of the next nodes
x1, y1 = next_node1["x"], next_node1["y"]
x2, y2 = next_node2["x"], next_node2["y"]

# Calculate the distance between the next nodes
distance = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

# Calculate the diagonal of a robot
width, length = (
    6.3,
    14.3,
)  # Adjusted to the unit of the Cartesian plane (1 unit = 100 mm)
diagonal = math.sqrt(width**2 + length**2)

# Calculate the threshold for collision
threshold = diagonal  # Since both robots are of the same size
```

#### Global Collision Evaluation
We use our defined proximity function to calculate collisions for all pairs of robots in their next time-step whenever we recieve a robot state update.

We want to detect collision one time-step earlier so we can send the appropriate signal and prevent the collision ahead of time, instead of finding out that a collision had happened after a particular robot moved.

**Efficient Robot Signaling**

We want to find the robot that's causing the most number of collisions and send a pause signal to it. It is in-efficient to send one pause signal for each pair of collision we detect. This approach results in the minimum number of robots that need to be stopped.

We implement a greedy algorithm that picks the robot with the maximum number of collisions each time until we have figured out all the robots we want to pause to make our global state collision free in the next time-step.

```python
# Iteratively resolve collisions globally
while collision_map:
    # Find the robot with the most potential collisions
    robot_to_pause = max(
        collision_map, key=lambda robot: len(collision_map[robot])
    )

    # Pause the robot and send the command
    self.send_command(robot_to_pause, "pause")

    # Remove all related collision pairs
    for robot in collision_map[robot_to_pause]:
        collision_map[robot].remove(robot_to_pause)
        if not collision_map[robot]:
            del collision_map[robot]
    del collision_map[robot_to_pause]
```

### Collision Resolution Algorithms
After we detect collisions and appropirately send the pause signals to the minimum number of robots needed to resolve the collision scenario, we also need to come up with an algorithm to resume old and previously paused robots.


#### Dependency Resolution:

When a robot is paused, add entries to a dependency map indicating which robots it has potential collisions with.

Whenever a robot moves, update the dependency map to remove any resolved dependencies.

After updating the dependencies, check the dependency map to find any robots that no longer have any dependencies and resume them.

- Pros:
    - Efficient: Only needs to check dependencies when a robot moves, not all possible collisions.
    - Accurate: Only resumes robots when it is safe to do so.
- Cons:
    - Complexity: Requires maintaining and updating a dependency relation, which requires using a graph DS to implement efficiently, adding complexity to the implementation.

#### Periodic Re-evaluation:

For each paused robot, check the current positions of the other robots that it had potential collisions with.

If these robots have moved to positions where they no longer pose a threat of collision, resume the paused robot.

We will need to run this periodic re-eval in a separate thread in our collision monitor.

- Pros:
    - Simple: Easy to implement, just periodically check each paused robot.
    - Robust: Can handle changes in robot paths or other unexpected events.
- Cons:
    - Inefficient: Needs to check each paused robot at regular intervals, even if no relevant changes have occurred.
    - Latency: There might be a delay in resuming robots since it’s based on periodic checks.

#### Event-Driven Re-evaluation:

Whenever a robot moves, check whether this movement resolves any potential collisions with paused robots.
Robot Pausing/Resuming:

Whenever a robot is paused or resumed, check whether this affects any paused robots.

- Pros:
    - Efficient: Only re-evaluates when a relevant event occurs.
    - Responsive: Can immediately resume robots when it becomes safe to do so.
- Cons:
    - Complexity: Requires identifying and handling all relevant events, which can be complex.
    - Latency: When running on each update, running both full collision detection and full resolution re-eval will make each iteration of the detector slow.

Given the time constraints and keeping a balance with efficient collision resolution, we opt for the **dependency resolution** algorithm. We can make it easier to implement by using hash-maps/dicts instead of implementing it with graphs.

We can combine this approach with periodic re-evaluation which will have a separate thread/service at a large scale to efficiently deal with 100s of robots.

**Deadlock Scenarios**

There is also a possiblity of reaching a deadlock state where 2 robots are in each other's dependency list and waiting for each other to resume. We will have to implement a simple deadlock resolution algorithm that will detect the cycle in the dependecy map and pick one robot to resume.

This will increase the time complexity of our algorithm (we have to cross check all keys in the dependency map with itself) but it will be easier to implement and easier to extend/update later on when we need to handle larger scales using Graphs.

```python
def resume_robots(self, moved_robot_id):
    for paused_robot, dependencies in list(self.dependencies.items()):

        dependencies.discard(
            moved_robot_id
        )  # Remove the moved robot from the dependencies of paused robots

        # using graphs can reduce the complexity of dependency resolution
        def is_in_dependency_list(robot_id):
            return any(robot_id in deps for deps in self.dependencies.values())

        # Check for potential deadlock
        if all(is_in_dependency_list(dep) for dep in dependencies):

            # Resolve deadlock by choosing one robot to resume
            robot_to_resume = self.resolve_deadlock(
                [paused_robot] + list(dependencies)
            )
            self.resume_robot(robot_to_resume)

        # If a paused robot no longer has any dependencies, resume it
        if not dependencies:
            self.resume_robot(paused_robot)
```

## System Architecture
Discussion about the overall solution proposed, its components, and how they interact to solve the problem.

## Testing and Validation
### Unit Tests
Description and results of the unit tests performed on various components of the project.

### Validation
Discussion about the validation of the overall system, including any manual testing and the outcomes.

## Scalability Considerations
Discussion about how the design can scale and considerations and modifications needed for large scale implementations.

### Large Scale Collision Detection
Discussion about designing solutions for large-scale collision detection and how the current solution can be adapted or modified for it.

## Theoretical Discussions
### Delays in State Messages
Discussion on considerations and design adaptations needed for delays in state messages due to poor internet connection in factories.

### Handling Dead-Zones
Exploration of potential edge cases arising from dead-zones in the factory and strategies and design modifications to handle them.

### Limitations of Collision Monitor
Discussion about scenarios where the Collision Monitor might not be effective in avoiding collisions/deadlocks and the inherent limitations of the reactive system.

### Proactive Approaches for Collision Avoidance
Discussion and exploration of other approaches that could be implemented to proactively avoid collisions, and how they would be implemented.

## Conclusion
Final thoughts, summary of the project outcomes, and potential future work.

