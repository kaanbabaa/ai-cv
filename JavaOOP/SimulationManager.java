package simulation;

import mod.Vehicle;
import mod.Route;
import mod.Flow;
import mod.TrafficLight;
import mod.SumoPolygon;
import mod.ParkingArea;
import reporting.CsvReportGenerator;
import utils.Colors;
import exceptions.SimulationManagerException;
import exceptions.TrafficLightException;
import exceptions.VehicleClassException;
import exceptions.RouteClassException;
import exceptions.FlowClassException;
import java.io.IOException;

import java.util.List;
import java.util.ArrayList;
import org.eclipse.sumo.libtraci.*;
import java.util.Random;
import java.util.Map;
import java.util.HashMap;
import java.util.Set; // HashSet (daha hızlı arama için)
import java.util.concurrent.ConcurrentHashMap;
import java.util.HashSet; // HashSet

public class SimulationManager {
	
	private final Map<String, Vehicle> activeVehicles;
	private final Map<String, TrafficLight> activeLights;
	private final Map<String, Route> activeRoutes;
	private final CsvReportGenerator vehicleReporter;
	private final CsvReportGenerator trafficLightReporter;
	private final List<List<double[]>> laneShapes;
	private final List<String> allEdgeIds;
	private final List<SumoPolygon> mapPolygons;
	private final List<ParkingArea> parkingAreaPolygons;
	private Random random;
	
	private static final String SUMO_BINARY = "sumo";
	private static final String CONFIG_FILE = "/Users/kaanbaba/sumo/examples/map1/osm.sumocfg";
	
	private double minX;
	private double minY;
	private double maxX;
	private double maxY;
	
	public SimulationManager() throws SimulationManagerException {
		
		this.activeVehicles = new ConcurrentHashMap<>();
		this.activeLights = new ConcurrentHashMap<>();
		this.activeRoutes = new ConcurrentHashMap<>();
		this.laneShapes = new ArrayList<>();
		this.allEdgeIds = new ArrayList<>();
		this.mapPolygons = new ArrayList<>();
		this.parkingAreaPolygons = new ArrayList<>();
		this.random = new Random();
		
		try {
			
            String vehicleHeader = "Time;VehicleID;Speed_ms;X_Coord;Y_Coord";
            this.vehicleReporter = new CsvReportGenerator("vehicle_report.csv", vehicleHeader);
            
            String lightHeader = "Time;LightID;ProgramID;CurrentPhase;Duration";
            this.trafficLightReporter = new CsvReportGenerator("trafficlight_report.csv", lightHeader);
            
		} catch (IOException e) {
			throw new SimulationManagerException("CSV reporter could not start: " + e);
		}
	}

	public void startSimulation() throws SimulationManagerException {
			String[] sumoArgs = {
					SUMO_BINARY,
					"-c", CONFIG_FILE,
					"--start"
			};
				
		try {
			//Simulation.preloadLibraries();
			Simulation.start(new StringVector(sumoArgs));
			System.out.println("SUMO connection established and simulation started!");
		} catch (Exception e) {throw new SimulationManagerException("SUMO simulation cant be started: " + e);}
	}
	
	public void closeSimulation() throws SimulationManagerException {
		if(vehicleReporter != null) vehicleReporter.close();
		if(trafficLightReporter != null) trafficLightReporter.close();
		
		try {
			Simulation.close();
			System.out.println("Simulation ended!");
		} catch(Exception e) {
			throw new SimulationManagerException("Error during closing the simulation: " + e.getMessage());
		}
	}
	
	public void runStep() throws Exception {
		
		Simulation.step();
	
		StringVector arrivedIdsVector = Simulation.getArrivedIDList();
	
		if(arrivedIdsVector.size() > 0) {
			Set<String> arrivedIds = new HashSet<>(arrivedIdsVector);
			for(String id : arrivedIds) {
				activeVehicles.remove(id);
			}
			System.out.println("Cleaning: " + arrivedIds.size() + " vehicle deleted.");
		}
		
		for(Vehicle veh : activeVehicles.values()) {
			try {
				veh.updateTelemetry();
				vehicleReporter.writeVehicleData(veh);
			} catch (Exception ex) {
				System.err.println("Error, VehicleId: " + veh.getId() + " cant be updated" + ex.getMessage());
			}
		}
		
		for(TrafficLight tl : activeLights.values()) {
			
			try {
				tl.updateState();
				trafficLightReporter.writeTrafficLightData(tl);
				
				String stuckLane = tl.getMostCongestedLane();
				if(stuckLane != null) {
					int saviorPhase = tl.getGreenPhaseForLane(stuckLane);
					if(saviorPhase != -1) {
						if(tl.getCurrentPhase() == saviorPhase) tl.setPhaseDuration(7.0);
						else {
							tl.setPhase(saviorPhase);
							tl.setPhaseDuration(12.0);
						}
					}
				}
				
				
			} catch (Exception e) {
				System.err.println("Error, " + tl.getGuiId() + " cant be updated: " + e.getMessage());
			}
		}
		
		for(ParkingArea cs : parkingAreaPolygons) {
			
			try {
				cs.updateState();
			} catch (Exception e) {
				System.err.println("Error, " + cs.getId() + " cant be updated: " + e.getMessage());
			}
		}
	}
	
	public void addVehicle(String id, String routeId, String vehType) throws SimulationManagerException {
		try {
			Route routeToUse = getRoute(routeId);
			if(routeToUse == null) {
				throw new SimulationManagerException("Route doesnt exists: " + routeId);
			}
			Vehicle newVehicle = new Vehicle(id, routeToUse, vehType);
			activeVehicles.put(newVehicle.getId(), newVehicle);
			System.out.println("MANAGER: Vehicle " + id + " is created and added to list.");
		} catch (VehicleClassException e) {
			throw new SimulationManagerException("Error during adding the vehicle to SUMO: " + id, e);
		}
	}
	
	public void addVehicle(String id, String routeId, String vehType, TraCIColor color) throws SimulationManagerException {
		try {
			Route routeToUse = getRoute(routeId);
			if(routeToUse == null) {
				throw new SimulationManagerException("Route doesnt exists: " + routeId);
			}
			Vehicle newVehicle = new Vehicle(id, routeToUse, vehType, color);
			activeVehicles.put(newVehicle.getId(), newVehicle);
			System.out.println("MANAGER: Vehicle " + id + " is created and added to list.");
		} catch (VehicleClassException e) {
			throw new SimulationManagerException("Error during adding the vehicle to SUMO: " + id, e);
		}
	}
	
	public void addVehicle(String id, Route routeId, String vehType) throws SimulationManagerException {
		if(routeId == null) {
			throw new SimulationManagerException("Route is null/empty. Cannot add vehicle: " + id);
		}
		try {
			Vehicle newVehicle = new Vehicle(id,routeId.getId(),vehType);
			activeVehicles.put(newVehicle.getId(),newVehicle);
			System.out.println("MANAGER: Vehicle " + id + " is created and added to list.");
		} catch (VehicleClassException e) {
			throw new SimulationManagerException("Error during adding the vehicle to SUMO: " + id, e);
		}
	}
	
	public void addVehicle(String id, Route routeId, String vehType, TraCIColor color) throws SimulationManagerException {
		if(routeId == null) {
			throw new SimulationManagerException("Route is null/empty. Cannot add vehicle: " + id);

		}
		try {
			Vehicle newVehicle = new Vehicle(id, routeId.getId(), vehType, color);
			activeVehicles.put(newVehicle.getId(), newVehicle);
			System.out.println("MANAGER: Vehicle " + id + " is created and added to list.");
		} catch (VehicleClassException e) {
			throw new SimulationManagerException("Error during adding the vehicle to SUMO: " + id, e);
		}
	}
	
	public void setColor(String id, TraCIColor color) throws SimulationManagerException {
		try {
			Vehicle veh = activeVehicles.get(id);
			
			if(veh != null) {
				veh.setColor(color);
				System.out.println("MANAGER: Vehicle " + id + " color adjusted.");
			} else {
				throw new SimulationManagerException("Vehicle Id not found: " + id);
			}
		} catch (VehicleClassException e) {
			throw new SimulationManagerException("Error during setting the color: " + id, e);
		}
	}
	
	public void setSpeed(String id, double speed) throws SimulationManagerException {
		try {
			Vehicle veh = activeVehicles.get(id);
			if(veh != null) {
				veh.setSpeed(speed);
				System.out.println("MANAGER: Vehicle " + id + " speed adjusted.");
			} else {
				throw new SimulationManagerException("Vehicle Id not found: " + id);
			}
		} catch(VehicleClassException e) {
			throw new SimulationManagerException("Error during setting the speed: " + id, e);
		}
	}
	
	public Route createAndGetRoute(String routeId) throws SimulationManagerException {
		
		if(activeRoutes.containsKey(routeId) ) {
			return activeRoutes.get(routeId);
		}	
		try {
			Route newRoute = new Route(routeId);
			activeRoutes.put(newRoute.getId(), newRoute);
			System.out.println("MANAGER: Route " + routeId + " is created succesfully.");
			return newRoute;
		} catch(RouteClassException e) {
			throw new SimulationManagerException("Route doesn`t exists: " + routeId, e);
		}
	}
	
	public void importRoutes() throws SimulationManagerException {
		try {
			StringVector routeIdVector = org.eclipse.sumo.libtraci.Route.getIDList();
			if(!routeIdVector.isEmpty()) {
			
				for(String id : routeIdVector) {
					Route newRoute = new Route(id);
					activeRoutes.put(id, newRoute);
				}
			}
			System.out.println("Importing routes is succesful.");
		} catch (Exception e) {
			throw new SimulationManagerException("Error while importing routes:  " + e.getMessage(), e);
		}
	}
	
	public Route getRoute(String routeId) {
		return activeRoutes.get(routeId);
	}
	
	public void triggerFlow(String flowId, String routeId, String vehType, int batchSize) throws SimulationManagerException {
		try {
			Route routeToUse = activeRoutes.get(routeId);
			
			if(routeToUse == null) {
				throw new SimulationManagerException("Route doesnt exists: " + routeId);
			}
			
			Flow flow = new Flow(flowId, routeToUse, vehType, batchSize);
			System.out.println("MANAGER: Flow " + flowId + " triggered...");
			
			List<Vehicle> newVehicles = flow.injectBatch();
			
			for(Vehicle v : newVehicles) {
				activeVehicles.put(v.getId(), v);
			}
			System.out.println("MANAGER: " + newVehicles.size() + " vehicles added from the Flow.");
		} catch (FlowClassException e) {
			throw new SimulationManagerException("MANAGER ERROR: flow isn`t triggered: " + flowId, e);
		}
	}
	
	public void triggerFlow(String flowId, Route route, String vehType, int batchSize) throws SimulationManagerException {
		try {
			if(route == null) {
				throw new SimulationManagerException("Route doesn`t exists: " + route);
			}
			
			Flow flow = new Flow(flowId, route.getId(), vehType, batchSize);
			System.out.println("MANAGER: Flow " + flowId + " triggered...");
			
			List<Vehicle> newVehicles = flow.injectBatch();
			
			for(Vehicle v : newVehicles) {
				activeVehicles.put(v.getId(), v);
			}
			System.out.println("MANAGER: " + newVehicles.size() + " vehicles added from the Flow.");
		} catch (FlowClassException e) {
			throw new SimulationManagerException("MANAGER ERROR: flow isn`t triggered: " + flowId, e);
		}
	}
	
	public void triggerFlow(String flowId, String routeId, String vehType, int batchSize, TraCIColor color) throws SimulationManagerException {
		try {
			Route routeToUse = activeRoutes.get(routeId);
			
			if(routeToUse == null) {
				throw new SimulationManagerException("Route doesnt exists: " + routeId);
			}
			
			Flow flow = new Flow(flowId, routeToUse, vehType, batchSize);
			System.out.println("MANAGER: Flow " + flowId + " triggered...");
			
			List<Vehicle> newVehicles = flow.injectBatch(color);
			
			for(Vehicle v : newVehicles) {
				activeVehicles.put(v.getId(), v);
			}
			System.out.println("MANAGER: " + newVehicles.size() + " vehicles added from the Flow.");
		} catch (FlowClassException e) {
			throw new SimulationManagerException("MANAGER ERROR: flow isn`t triggered: " + flowId, e);
		}
	}
	
	public void triggerFlow(String flowId, Route route, String vehType, int batchSize, TraCIColor color) throws SimulationManagerException {
		try {
			if(route == null) {
				throw new SimulationManagerException("Route doesn`t exists: " + route);
			}
			
			Flow flow = new Flow(flowId, route.getId(), vehType, batchSize);
			System.out.println("MANAGER: Flow " + flowId + " triggered...");
			
			List<Vehicle> newVehicles = flow.injectBatch(color);
			
			for(Vehicle v : newVehicles) {
				activeVehicles.put(v.getId(), v);
			}
			System.out.println("MANAGER: " + newVehicles.size() + " vehicles added from the Flow.");
		} catch (FlowClassException e) {
			throw new SimulationManagerException("MANAGER ERROR: flow isn`t triggered: " + flowId, e);
		}
	}
	
	public void importTrafficLights() throws SimulationManagerException {
		int count = 0;
		try {
			StringVector tlIdVector = org.eclipse.sumo.libtraci.TrafficLight.getIDList();
			if(!tlIdVector.isEmpty()) {
				for(String id : tlIdVector) {
					String clearId = "tl_" + count; 
					TrafficLight newTl = new TrafficLight(id, clearId);
					
					activeLights.put(clearId, newTl);
					count++;
				}
			}
			System.out.println("Traffic Lights added to activeLights succesfully.");
		} catch (Exception e) {
			throw new SimulationManagerException("MANAGER ERROR: Error during importing the traffic lights: " + e.getMessage());
			
		}
	}
	
	public void setPhase(String easyId, int phaseIndex) throws SimulationManagerException {
		try {
			
			TrafficLight tl = activeLights.get(easyId);
			if(tl == null) {
				throw new SimulationManagerException("MANAGER ERROR: Traffic light doesnt exists: " + easyId);
			}
			tl.setPhase(phaseIndex);
			System.out.println("MANAGER: Traffic light " + tl.getId() + " phase setted to " + phaseIndex);
			
		} catch (TrafficLightException e) {
			throw new SimulationManagerException("MANAGER ERROR: Phase could not be set: " + easyId, e);
		}
	}
	
	public void setPhaseDuration(String id, double duration) throws SimulationManagerException {
		try {
			
			TrafficLight tl = activeLights.get(id);
			if(tl == null) {
				throw new SimulationManagerException("MANAGER ERROR: Traffic light doesnt exists: " + id);
			}
			tl.setPhaseDuration(duration);
			System.out.println("MANAGER: Traffic light " + tl.getGuiId() + " updated phase duration: " + duration);
			
		} catch (TrafficLightException e) {
			throw new SimulationManagerException(" MANAGER ERROR: Phase duration could not be set: " + id, e);
		}
	}
	
	public Map<String, Vehicle> getActiveVehicles() {return activeVehicles;}
	
	public Map<String, TrafficLight> getActiveLights() {return activeLights;}
	
	public void calculateMapBounds() throws Exception {
		System.out.println("Calculating map bounds...");
		TraCIPositionVector rawPositions = Simulation.getNetBoundary();
		TraCPositionVector positions = rawPositions.getValue();
		minX = positions.get(0).getX();
		minY = positions.get(0).getY();
		maxX = positions.get(1).getX();
		maxY = positions.get(1).getY();
		
	}
	
	public double getMinX() {
		return minX;
	}
	
	public double getMinY() {
		return minY;
	}
	
	public double getMaxX() {
		return maxX;
	}
	
	public double getMaxY() {
		return maxY;
	}
	
	public void importRoadNetwork() throws SimulationManagerException {
		try {
			System.out.println("THREAD: Road network (lane shapes) are downloading... ");
			StringVector laneIds = Lane.getIDList();
			
			for (String laneId : laneIds) {
				TraCIPositionVector shapeWrapper = Lane.getShape(laneId);
				TraCPositionVector shape = shapeWrapper.getValue();
			
				List <double[]> currentLanePoints = new ArrayList<>();
			
				for(int j = 0; j < shape.size(); j++) {
					TraCIPosition pos = shape.get(j);
					currentLanePoints.add(new double[] {pos.getX(), pos.getY()});
				}
				laneShapes.add(currentLanePoints);
			}
			System.out.println("Road network downloaded: " + laneShapes.size() + " lanes exists.");
		} catch (Exception e) {
			throw new SimulationManagerException("Road network could not be downloaded: " + e.getMessage(), e);
		}
	}
	
	public List<List<double[]>> getLaneShapes() {return laneShapes;}
	
	public void loadAllEdges() throws SimulationManagerException {
		try {
			StringVector edges = Edge.getIDList();
			for(int i = 0; i < edges.size(); i++) {
				String edgeId = edges.get(i);
				if(!edgeId.startsWith(":")) { allEdgeIds.add(edgeId);}
			}
			System.out.println("System: " + allEdgeIds.size() + " possible edges exists.");
		} catch (Exception e) {
			throw new SimulationManagerException("Edges are not downloaded: " + e.getMessage(), e);
		}
	}
	
	private Route createDynamicRoute(String startEdgeId, String endEdgeId) throws SimulationManagerException {
		String newRouteId = "route_" + startEdgeId + "to" + endEdgeId;
		if(activeRoutes.containsKey(newRouteId)) {
			return activeRoutes.get(newRouteId);
		}
		try {
			TraCIStage stage = Simulation.findRoute(startEdgeId, endEdgeId, "DEFAULT_VEHTYPE", -1.0, 0);
			StringVector routeEdges = stage.getEdges();
			
			if(routeEdges.size() == 0) {
				throw new SimulationManagerException("Route could not find: " + startEdgeId + " -> " + endEdgeId);
			}
			org.eclipse.sumo.libtraci.Route.add(newRouteId, routeEdges);
			Route newRouteObj = createAndGetRoute(newRouteId);
			System.out.println("MANAGER: Dynamic Route Created!");
			return newRouteObj;
		} catch (Exception e) {
			throw new SimulationManagerException("MANAGER: Dynamic Route could not be created: " + newRouteId, e);
		}
	}
	
	public Route createRandomAutonomousRoute() {
		if(allEdgeIds.isEmpty()) return null;
		int maxRetries = 10;
		for (int i = 0; i < maxRetries; i++) {
			try {
				String startEdge = allEdgeIds.get(random.nextInt(allEdgeIds.size()));
				String endEdge = allEdgeIds.get(random.nextInt(allEdgeIds.size()));
				if(startEdge.equals(endEdge)) continue;
				
				Route route = createDynamicRoute(startEdge, endEdge);
				
				if(route != null) {
					System.out.println("MANAGER: Autonomous Route finded (" + (i+1) + ". try) " + startEdge + " -> " + endEdge);
					return route;
				}
			} catch (Exception e) {
				System.err.println("MANAGER: Try " + (i+1) + " for finding autonomous route failed.");
			}
		} 
		System.out.println("MANAGER: Error, in " + maxRetries + " try appropiate route could not find.");
		return null;
	}
	
	
	public void createRandomVehicle() throws SimulationManagerException {
		String id = "RandomVehicle_" + random.nextDouble();
		try {
			Route randomRoute = createRandomAutonomousRoute();
			addVehicle(id, randomRoute, "DEFAULT_VEHTYPE");
			setColor(id, Colors.getRandomColor());
			
		} catch (Exception e) {
			throw new SimulationManagerException("MANAGER: Error during creating a random vehicle: " + e);
		}
	}
	
	public void importPolygons() throws SimulationManagerException {
		try {
			System.out.println("MANAGER: Downloading polygons.");
			StringVector polyIds = Polygon.getIDList();
			
			for(String id : polyIds) {
				TraCIPositionVector rawShape = Polygon.getShape(id);
				TraCPositionVector shape = rawShape.getValue();
				
				List<double[]> points = new ArrayList<>();
				for(int i = 0; i < shape.size(); i++) {
					points.add(new double[] {shape.get(i).getX(), shape.get(i).getY()});
				}
				
				TraCIColor tc = Polygon.getColor(id);
				java.awt.Color color = new java.awt.Color(tc.getR(), tc.getG(), tc.getB(), tc.getA());
				
				boolean isFilled = Polygon.getFilled(id);
				
				mapPolygons.add(new SumoPolygon(id, points, color, isFilled));
			}
			System.out.println("MANAGER: " + mapPolygons.size() + " polygons downloaded.");
		} catch(Exception e) {
			throw new SimulationManagerException("Polygons could not be downloaded: " + e.getMessage());
		}
	}
	
	public List<SumoPolygon> getMapPolygons() { return mapPolygons;}
	
	public void importCsPolygons() throws SimulationManagerException{
		try {
			System.out.println("MANAGER: Downloading Charging station Polygons.");
			StringVector csIds = org.eclipse.sumo.libtraci.ChargingStation.getIDList();
			
			for(String id: csIds) {
				parkingAreaPolygons.add(new ParkingArea(id));
			}
			System.out.println("MANAGER: " + csIds.size() + " charging station imported.");
		} catch (Exception e) {
			throw new SimulationManagerException("MANAGER: Error during downloading the Charging station: " + e.getMessage());
		}
	}
	
	public List<ParkingArea> getParkingAreaPolygons() { return parkingAreaPolygons;}
	
	
	public void switchTrafficLightToRed(String lightId) throws SimulationManagerException {
	    TrafficLight tl = activeLights.get(lightId);
	    if (tl == null) {
	        throw new SimulationManagerException("Traffic Light doesnt exists: " + lightId);
	    }
	    
	    try {
	        if (!tl.isRedPhase()) {
	            tl.switchToNextRed();
	        } else {
	            System.out.println("MANAGER: " + lightId + " already red.");
	        }
	    } catch (Exception e) {
	        throw new SimulationManagerException("Traffic Light could not be changed: " + e.getMessage(), e);
	    }
	}
	
	public void switchTrafficLightToGreen(String lightId) throws SimulationManagerException {
	    TrafficLight tl = activeLights.get(lightId);
	    if (tl == null) {
	        throw new SimulationManagerException("Traffic Light doesnt exists: " + lightId);
	    }
	    
	    try {
	        if (!tl.isGreenPhase()) {
	            tl.switchToNextGreen();
	        } else {
	            System.out.println("MANAGER: " + lightId + " already red.");
	        }
	    } catch (Exception e) {
	        throw new SimulationManagerException("Traffic Light could not be changed: " + e.getMessage(), e);
	    }
	}
	
	public Object[] getActiveRoutes() {	return activeRoutes.keySet().toArray();	}
	
	public String getTlProgramDefinition(String id) throws SimulationManagerException {
		TrafficLight tl = getActiveLights().get(id); 
		if(tl == null) throw new SimulationManagerException("MANAGER: Error during getting program definitions: " + id);	
		return tl.getProgramDefinition();
		}
	
	public void startStressTest(int vehCount) throws SimulationManagerException {
		 new Thread(() -> {
			 
			 for(int i = 0; i < vehCount; i++) {
				 try {
					 createRandomVehicle();
					 Thread.sleep(200);
				 } catch(Exception e) { }
			 }
		 }).start();
		 
	}