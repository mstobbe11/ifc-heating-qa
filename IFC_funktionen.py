# -*- coding: utf-8 -*-
"""
Created on Fri May 13 11:36:25 2022
@author: marcs
"""
import os #Paket zur Ordnersteuerung

import uuid              #Paket zur Erstellung von einmaligen GUIDs
import ifcopenshell      #Paket um IFC Dateien zu bearbeiten
import ifcopenshell.geom #Paket um Geometrie von IFC Dateien zu erfassen
import graphviz          #Paket zur grafischen Darstellung
import math              #Paket für Berechnungen

O = 0., 0., 0.           #Achsen für Geometriedummy
X = 1., 0., 0.           #Achsen für Geometriedummy
Y = 0., 1., 0.           #Achsen für Geometriedummy
Z = 0., 0., 1.           #Achsen für Geometriedummy

def vorschlagsmodell(art, flaeche, beheizte_flaeche, erde, grundwasser, laerm, kosten, warmwasser):
    gebaeude = art
    antworten = []
    global anlage
    if float(flaeche)*2 >= float(beheizte_flaeche):
        antworten.append(1)
    else: antworten.append(0)
    if int(erde) == 1:
        antworten.append(1)
    else: antworten.append(0)
    if int(grundwasser) == 1:
        antworten.append(1)
    else: antworten.append(0)
    if int(laerm) == 1:
        antworten.append(1)
    else: antworten.append(0)
    if int(kosten) == 1:
        antworten.append(1)
    else: antworten.append(0)
    if int(warmwasser) == 1:
        antworten.append(1)
    else: antworten.append(0)
    if antworten[1] == 1:
        anlage = "Erdwärmesonde"
    elif antworten[2] == 1:
        anlage = "Grundwassersonde"
    elif antworten[0] == 1:
        anlage = "Erdwärmekollektor"
    else:
        anlage = "Luftwärmepumpe"
    if antworten[5] == 1:
        anlage += " mit Warmwasser"
    else:
        anlage += " ohne Warmwasser"
    file = open('anlage.txt', 'a+')
    file.write(anlage)
    file.close()
    
### Zwei-Rohr-System
def abgleich_zweirohr(ifc_system, heizkoerper, rohr):
    #Aufnahme der Heizflächen
    for property_set in heizkoerper.IsDefinedBy:
        if property_set.RelatingPropertyDefinition.Name == "Heizkoerper_Auslegung":
            betriebsleistung = property_set.RelatingPropertyDefinition.HasProperties[3].NominalValue.wrappedValue
            vorlauftemperatur = property_set.RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue
            ruecklauftemperatur =property_set.RelatingPropertyDefinition.HasProperties[5].NominalValue.wrappedValue        
    #Aufnahme Rohrverbindung
    for property_set in rohr.IsDefinedBy:
        if property_set.RelatingPropertyDefinition.Name == "Rohrteil_Basismengen":
            rohrlaenge = property_set.RelatingPropertyDefinition.Quantities[0].LengthValue
            rohrinnenabmessung = property_set.RelatingPropertyDefinition.Quantities[3].LengthValue
    ### Grundwerte
    dichte_w = 995 #kg/m³
    kinematische_zaehigkeit = 0.724  #mm²/s
    waermekapazitaet_wasser = 1.16 #Wh/kg*K
    spreizung = vorlauftemperatur-ruecklauftemperatur
#   notwendiger_massenstrom = betriebsleistung/(spreizung*waermekapazitaet_wasser)    #kg/h
    notwendiger_volumenstrom = betriebsleistung/(spreizung*waermekapazitaet_wasser*dichte_w)  #m³/h
    rohrquerschnitt = math.pi*((rohrinnenabmessung/2)/1000)**2     #m²
    print(rohrquerschnitt)
    geschwindigkeit_rohr = (notwendiger_volumenstrom/3600)/rohrquerschnitt   #m/s
    print(geschwindigkeit_rohr)
    reynoldzahl = (geschwindigkeit_rohr*(rohrinnenabmessung/1000))/(kinematische_zaehigkeit/1000000)
    if reynoldzahl <= 2300:
        reibungszahl = 64/reynoldzahl     #bei Reynoldzahl < 2300
    else:
        reibungszahl = 0.3164/(reynoldzahl**2) #bei Reynoldzahl > 2300
    rohrreibungswiderstand = (reibungszahl*dichte_w*(geschwindigkeit_rohr**2))/(rohrinnenabmessung/1000*2)    #Pa/m
    druckverlust_leitung = rohrreibungswiderstand*(rohrlaenge/1000)
    zf = 1.3*1.2*1.7
    print(druckverlust_leitung)
    gesamt = druckverlust_leitung*zf
    print(gesamt)
    #Ventil
    druckverluste_ventil = gesamt-(gesamt/1.7)             ###in Pascel
    av = druckverluste_ventil/gesamt
    druckverlust_themostat = druckverluste_ventil/100000   ###in bar
    kv = notwendiger_volumenstrom*math.sqrt(1/druckverlust_themostat)   #m³/h
    #Ergebnisse speichern
    for property_set in rohr.IsDefinedBy:
        if  property_set.RelatingPropertyDefinition.Name == "Rohrteil_Auslegung":
            property_set.RelatingPropertyDefinition.HasProperties[14].NominalValue.wrappedValue = reynoldzahl
            property_set.RelatingPropertyDefinition.HasProperties[15].NominalValue.wrappedValue = reibungszahl
            property_set.RelatingPropertyDefinition.HasProperties[16].NominalValue.wrappedValue = rohrreibungswiderstand
            property_set.RelatingPropertyDefinition.HasProperties[17].NominalValue.wrappedValue = gesamt
    for property_set in heizkoerper.IsDefinedBy:
        if  property_set.RelatingPropertyDefinition.Name == "Heizkoerper_Auslegung":
            property_set.RelatingPropertyDefinition.HasProperties[6].NominalValue.wrappedValue = notwendiger_volumenstrom
        if  property_set.RelatingPropertyDefinition.Name == "Thermostatventil_Auslegung":
            property_set.RelatingPropertyDefinition.HasProperties[0].NominalValue.wrappedValue = druckverlust_themostat
            property_set.RelatingPropertyDefinition.HasProperties[1].NominalValue.wrappedValue = gesamt
            property_set.RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue = av
            property_set.RelatingPropertyDefinition.HasProperties[3].NominalValue.wrappedValue = kv

### Zwei-Rohr-System
def abgleich_zweirohr(ifc_system, heizkoerper, rohr):
    #Aufnahme der Heizflächen
    for property_set in heizkoerper.IsDefinedBy:
        if property_set.RelatingPropertyDefinition.Name == "Heizkoerper_Auslegung":
            betriebsleistung = property_set.RelatingPropertyDefinition.HasProperties[3].NominalValue.wrappedValue
            vorlauftemperatur = property_set.RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue
            ruecklauftemperatur =property_set.RelatingPropertyDefinition.HasProperties[5].NominalValue.wrappedValue        
    #Aufnahme Rohrverbindung
    for property_set in rohr.IsDefinedBy:
        if property_set.RelatingPropertyDefinition.Name == "Rohrteil_Basismengen":
            rohrlaenge = property_set.RelatingPropertyDefinition.Quantities[0].LengthValue
            rohrinnenabmessung = property_set.RelatingPropertyDefinition.Quantities[3].LengthValue
    ### Grundwerte
    dichte_w = 995 #kg/m³
    kinematische_zaehigkeit = 0.724  #mm²/s
    waermekapazitaet_wasser = 1.16 #Wh/kg*K
    spreizung = vorlauftemperatur-ruecklauftemperatur
#   notwendiger_massenstrom = betriebsleistung/(spreizung*waermekapazitaet_wasser)    #kg/h
    notwendiger_volumenstrom = betriebsleistung/(spreizung*waermekapazitaet_wasser*dichte_w)  #m³/h
    rohrquerschnitt = math.pi*((rohrinnenabmessung/2)/1000)**2     #m²
    print(rohrquerschnitt)
    geschwindigkeit_rohr = (notwendiger_volumenstrom/3600)/rohrquerschnitt   #m/s
    print(geschwindigkeit_rohr)
    reynoldzahl = (geschwindigkeit_rohr*(rohrinnenabmessung/1000))/(kinematische_zaehigkeit/1000000)
    if reynoldzahl <= 2300:
        reibungszahl = 64/reynoldzahl     #bei Reynoldzahl < 2300
    else:
        reibungszahl = 0.3164/(reynoldzahl**2) #bei Reynoldzahl > 2300
    rohrreibungswiderstand = (reibungszahl*dichte_w*(geschwindigkeit_rohr**2))/(rohrinnenabmessung/1000*2)    #Pa/m
    druckverlust_leitung = rohrreibungswiderstand*(rohrlaenge/1000)
    zf = 1.3*1.2*1.7
    print(druckverlust_leitung)
    gesamt = druckverlust_leitung*zf
    print(gesamt)
    #Ventil
    druckverluste_ventil = gesamt-(gesamt/1.7)             ###in Pascel
    av = druckverluste_ventil/gesamt
    druckverlust_themostat = druckverluste_ventil/100000   ###in bar
    kv = notwendiger_volumenstrom*math.sqrt(1/druckverlust_themostat)   #m³/h
    #Ergebnisse speichern
    for property_set in rohr.IsDefinedBy:
        if  property_set.RelatingPropertyDefinition.Name == "Rohrteil_Auslegung":
            property_set.RelatingPropertyDefinition.HasProperties[14].NominalValue.wrappedValue = reynoldzahl
            property_set.RelatingPropertyDefinition.HasProperties[15].NominalValue.wrappedValue = reibungszahl
            property_set.RelatingPropertyDefinition.HasProperties[16].NominalValue.wrappedValue = rohrreibungswiderstand
            property_set.RelatingPropertyDefinition.HasProperties[17].NominalValue.wrappedValue = gesamt
    for property_set in heizkoerper.IsDefinedBy:
        if  property_set.RelatingPropertyDefinition.Name == "Heizkoerper_Auslegung":
            property_set.RelatingPropertyDefinition.HasProperties[6].NominalValue.wrappedValue = notwendiger_volumenstrom
        if  property_set.RelatingPropertyDefinition.Name == "Thermostatventil_Auslegung":
            property_set.RelatingPropertyDefinition.HasProperties[0].NominalValue.wrappedValue = druckverlust_themostat
            property_set.RelatingPropertyDefinition.HasProperties[1].NominalValue.wrappedValue = gesamt
            property_set.RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue = av
            property_set.RelatingPropertyDefinition.HasProperties[3].NominalValue.wrappedValue = kv

def abgleich_fbh_ustrang(ifc_system, heizflaeche, rohr):
    for property_set in heizflaeche.IsDefinedBy:
        if property_set.RelatingPropertyDefinition.Name == "Fussbodenheizung_Auslegung":
            betriebsleistung = property_set.RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue
            vorlauftemperatur = property_set.RelatingPropertyDefinition.HasProperties[3].NominalValue.wrappedValue
            ruecklauftemperatur =property_set.RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue        
    #Aufnahme Rohrverbindung
    for property_set in rohr.IsDefinedBy:
        if property_set.RelatingPropertyDefinition.Name == "Rohrteil_Basismengen":
            rohrlaenge = property_set.RelatingPropertyDefinition.Quantities[0].LengthValue/1000
            rohrinnenabmessung = property_set.RelatingPropertyDefinition.Quantities[3].LengthValue
    ### Grundwerte
    dichte_w = 995 #kg/m³
    kinematische_zaehigkeit = 0.724  #mm²/s
    waermekapazitaet_wasser = 1.16 #Wh/kg*K
    spreizung = vorlauftemperatur-ruecklauftemperatur
#   notwendiger_massenstrom = betriebsleistung/(spreizung*waermekapazitaet_wasser)    #kg/h
    notwendiger_volumenstrom = betriebsleistung/(spreizung*waermekapazitaet_wasser*dichte_w)  #m³/h
    rohrquerschnitt = math.pi*((rohrinnenabmessung/2)/1000)**2     #m²
    geschwindigkeit_rohr = (notwendiger_volumenstrom/3600)/rohrquerschnitt   #m/s
    reynoldzahl = (geschwindigkeit_rohr*(rohrinnenabmessung/1000))/(kinematische_zaehigkeit/1000000)
    if reynoldzahl <= 2300:
        reibungszahl = 64/reynoldzahl     #bei Reynoldzahl < 2300
    else:
        reibungszahl = 0.3164/(reynoldzahl**2) #bei Reynoldzahl > 2300
    rohrreibungswiderstand = (reibungszahl*dichte_w*(geschwindigkeit_rohr**2))/(rohrinnenabmessung/1000*2)    #Pa/m
    print(rohrreibungswiderstand)
    druckverlust_leitung1 = round(rohrreibungswiderstand*rohrlaenge*2, 2)
    zf = 1.5
    druckverlust_leitung = round(druckverlust_leitung1*zf, 2)
    print(druckverlust_leitung)
    #Ergebnisse speichern
    for property_set in rohr.IsDefinedBy:
        if  property_set.RelatingPropertyDefinition.Name == "Rohrteil_Auslegung":
            property_set.RelatingPropertyDefinition.HasProperties[13].NominalValue.wrappedValue = geschwindigkeit_rohr
            property_set.RelatingPropertyDefinition.HasProperties[14].NominalValue.wrappedValue = reynoldzahl
            property_set.RelatingPropertyDefinition.HasProperties[15].NominalValue.wrappedValue = reibungszahl
            property_set.RelatingPropertyDefinition.HasProperties[16].NominalValue.wrappedValue = rohrreibungswiderstand
            property_set.RelatingPropertyDefinition.HasProperties[17].NominalValue.wrappedValue = druckverlust_leitung
    for property_set in heizflaeche.IsDefinedBy:
        if  property_set.RelatingPropertyDefinition.Name == "Fussbodenheizung_Auslegung":
            property_set.RelatingPropertyDefinition.HasProperties[5].NominalValue.wrappedValue = notwendiger_volumenstrom


### Fußbodenheizung
def abgleich_fbh(ifc_system, heizflaeche, rohr):
    #Aufnahme der Heizflächen
    for property_set in heizflaeche.IsDefinedBy:
        if property_set.RelatingPropertyDefinition.Name == "Fussbodenheizung_Auslegung":
            betriebsleistung = property_set.RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue
            vorlauftemperatur = property_set.RelatingPropertyDefinition.HasProperties[3].NominalValue.wrappedValue
            ruecklauftemperatur =property_set.RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue        
    #Aufnahme Rohrverbindung
    for property_set in rohr.IsDefinedBy:
        if property_set.RelatingPropertyDefinition.Name == "Rohrteil_Basismengen":
            rohrlaenge = property_set.RelatingPropertyDefinition.Quantities[0].LengthValue
            rohrinnenabmessung = property_set.RelatingPropertyDefinition.Quantities[3].LengthValue
    ### Grundwerte
    dichte_w = 995 #kg/m³
    kinematische_zaehigkeit = 0.724  #mm²/s
    waermekapazitaet_wasser = 1.16 #Wh/kg*K
    spreizung = vorlauftemperatur-ruecklauftemperatur
#   notwendiger_massenstrom = betriebsleistung/(spreizung*waermekapazitaet_wasser)    #kg/h
    notwendiger_volumenstrom = betriebsleistung/(spreizung*waermekapazitaet_wasser*dichte_w)  #m³/h
    rohrquerschnitt = math.pi*((rohrinnenabmessung/2)/1000)**2     #m²
    geschwindigkeit_rohr = (notwendiger_volumenstrom/3600)/rohrquerschnitt   #m/s
    reynoldzahl = (geschwindigkeit_rohr*(rohrinnenabmessung/1000))/(kinematische_zaehigkeit/1000000)
    if reynoldzahl <= 2300:
        reibungszahl = 64/reynoldzahl     #bei Reynoldzahl < 2300
    else:
        reibungszahl = 0.3164/(reynoldzahl**2) #bei Reynoldzahl > 2300
    rohrreibungswiderstand = (reibungszahl*dichte_w*(geschwindigkeit_rohr**2))/(rohrinnenabmessung/1000*2)    #Pa/m
    druckverlust_leitung = rohrreibungswiderstand*rohrlaenge
    print(druckverlust_leitung)
    #zf = 1.3*1.2*1.7
    zf = 1.5
    av = 0.5
    
    gesamt = druckverlust_leitung*zf
    print(gesamt)
    #Ventil
    druckverluste_ventil1 = gesamt-(gesamt/1.7)             ###in Pascel
    #av = druckverluste_ventil1/gesamt
    druckverlust_ventil = druckverluste_ventil1/100000   ###in bar
    kv = notwendiger_volumenstrom*math.sqrt(1/druckverlust_ventil)   #m³/h
    #Ergebnisse speichern
    for property_set in rohr.IsDefinedBy:
        if  property_set.RelatingPropertyDefinition.Name == "Rohrteil_Auslegung":
            property_set.RelatingPropertyDefinition.HasProperties[13].NominalValue.wrappedValue = geschwindigkeit_rohr
            property_set.RelatingPropertyDefinition.HasProperties[14].NominalValue.wrappedValue = reynoldzahl
            property_set.RelatingPropertyDefinition.HasProperties[15].NominalValue.wrappedValue = reibungszahl
            property_set.RelatingPropertyDefinition.HasProperties[16].NominalValue.wrappedValue = rohrreibungswiderstand
            property_set.RelatingPropertyDefinition.HasProperties[17].NominalValue.wrappedValue = druckverlust_leitung
    for property_set in heizflaeche.IsDefinedBy:
        if  property_set.RelatingPropertyDefinition.Name == "Fussbodenheizung_Auslegung":
            property_set.RelatingPropertyDefinition.HasProperties[5].NominalValue.wrappedValue = notwendiger_volumenstrom
        if  property_set.RelatingPropertyDefinition.Name == "Heizungsverteiler_Auslegung":
            property_set.RelatingPropertyDefinition.HasProperties[0].NominalValue.wrappedValue = druckverluste_ventil1
            property_set.RelatingPropertyDefinition.HasProperties[1].NominalValue.wrappedValue = gesamt
            property_set.RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue = av
            property_set.RelatingPropertyDefinition.HasProperties[3].NominalValue.wrappedValue = kv


def schema1():
    ifc_file_schema = ifcopenshell.open('System.ifc')                      #File der Heizungsanlage öffnen
    connections = ifc_file_schema.by_type("IfcRelConnectsPorts") #IFCRELCONNECTSPORTS
    nests = ifc_file_schema.by_type("IfcRelNests") #IFCRELNESTS
    objekte = []
    for nest in nests:
        objekte.append(nest.RelatingObject)
    g = graphviz.Graph(format='png', filename='heizung1')
    #g = graphviz.Digraph('G', filename='Schema.gv')
    for objekt in objekte:
        if 'Pumpe -' in str(objekt):
            g.attr('node', shape='none', image = 'Pumpensymbol.png', imagescale='both', width='0.4', height= '0.4', fixedsize = 'True')
            g.node(objekt.Name, xlabel=objekt.Name, fontsize="10", label="")
        elif 'Waermepumpe' in str(objekt):
            g.attr('node', shape='box3d', image = '', imagescale='both', width='1.1', height= '0.7', fixedsize = 'True')
            g.node(objekt.Name, xlabel="", fontsize="12", label=objekt.Name, fontname="times-bold")
        elif 'eicher:Mit' in str(objekt):
            g.attr('node', shape='cylinder', image = '', imagescale='both', width='0.5', height= '0.5', fixedsize = 'True')
            g.node(objekt.Name, fontcolor='blue2', xlabel=objekt.Name, fontsize="12", label="", fontname="times-bold")
        elif '3-Wege-Ventil' in str(objekt):
            g.attr('node', shape='none', image = 'Ventil.png', imagescale='both', width='0.15', height= '0.15', fixedsize = 'True')
            g.node(objekt.Name, xlabel=objekt.Name, fontsize='10', label="")
        elif 'T-Stueck' in str(objekt):
            g.attr('node', shape='none', image = 'T_S.png', imagescale='both', width='0.15', height= '0.15', fixedsize = 'True')
            g.node(objekt.Name, xlabel=objekt.Name, fontsize="10", label="")
        elif 'Fussbodenheizung' in str(objekt):
            g.attr('node', shape='none', image = 'FB.png', imagescale='both', width='0.6', height= '0.6', fixedsize = 'True')
            g.node(objekt.Name, fontcolor='firebrick1', xlabel=objekt.Name, fontsize="12", label="")
        elif 'Verteiler-Heizkreis' in str(objekt):
            g.attr('node', shape='circle', image = '', width='0.5', height= '0.5', fixedsize = 'True')
            g.node(objekt.Name, xlabel=objekt.Name, fontsize="12", label="")
        elif 'Rohr -' in str(objekt):
            if objekt.IsNestedBy[0].RelatedObjects[0].ConnectedTo == ():
                g.attr('node', shape='doublecircle', width='0.3', height= '0.3', fixedsize = 'True', image='')
                g.node(objekt.Name, style='filled', xlabel=objekt.Name, fontsize="9", label="")
            elif objekt.IsNestedBy[0].RelatedObjects[1].ConnectedFrom == ():
                g.attr('node', shape='doublecircle', width='0.3', height= '0.3', fixedsize = 'True', image='')
                g.node(objekt.Name, style='filled', xlabel=objekt.Name, fontsize="9", label="")
        else:
            pass
    for verbindung in connections:
        if 'Rohr -' in verbindung.RelatedPort.Nests[0].RelatingObject.Name and verbindung.RelatedPort.Nests[0].RelatedObjects[0].ConnectedTo!= ():
            pass
        elif 'Rohr -' in verbindung.RelatingPort.Nests[0].RelatingObject.Name and verbindung.RelatingPort.Nests[0].RelatedObjects[1].ConnectedFrom!= ():
            if 'Pumpe' in verbindung.RelatingPort.Nests[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.Name or 'Pumpe' in verbindung.RelatedPort.Nests[0].RelatingObject.Name:
                g.edge(verbindung.RelatingPort.Nests[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.Name, verbindung.RelatedPort.Nests[0].RelatingObject.Name, dir='forward', arrowsize='0.5', color="red")
            elif 'Ventil' in verbindung.RelatingPort.Nests[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.Name or 'Ventil' in verbindung.RelatedPort.Nests[0].RelatingObject.Name:
                g.edge(verbindung.RelatingPort.Nests[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.Name, verbindung.RelatedPort.Nests[0].RelatingObject.Name, dir='forward', arrowsize='0.5', color="red")
            else:
                g.edge(verbindung.RelatingPort.Nests[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.Name, verbindung.RelatedPort.Nests[0].RelatingObject.Name, dir='forward', arrowsize='0.5', color="blue")
        else:
            if 'Ruecklauf' in verbindung.RelatingPort.Nests[0].RelatingObject.Name or 'Ruecklauf' in verbindung.RelatedPort.Nests[0].RelatingObject.Name:
                g.edge(verbindung.RelatingPort.Nests[0].RelatingObject.Name, verbindung.RelatedPort.Nests[0].RelatingObject.Name, dir='forward', arrowsize='0.5', color="blue")
            else:
                g.edge(verbindung.RelatingPort.Nests[0].RelatingObject.Name, verbindung.RelatedPort.Nests[0].RelatingObject.Name, dir='forward', arrowsize='0.5', color="red")
    g.render('heizung1', engine='neato')
    
def schema2():
    ifc_file_schema = ifcopenshell.open('System_verbunden.ifc')
    connections = ifc_file_schema.by_type("IfcRelConnectsPorts") #IFCRELCONNECTSPORTS
    nests = ifc_file_schema.by_type("IfcRelNests") #IFCRELNESTS
    objekte = []
    for nest in nests:
        objekte.append(nest.RelatingObject)
        g = graphviz.Graph(format='png', filename='heizung2')
        #g = graphviz.Digraph('G', filename='Schema.gv')
    for objekt in objekte:
        if 'Pumpe -' in str(objekt):
            g.attr('node', shape='none', image = 'Pumpensymbol.png', imagescale='both', width='0.3', height= '0.3', fixedsize = 'True')
            g.node(objekt.Name, xlabel=objekt.Name, fontsize="10", label="")
        elif 'Wärmepumpe' in str(objekt):
            g.attr('node', shape='box3d', image = '', imagescale='both', width='0.8', height= '0.8', fixedsize = 'True')
            g.node(objekt.Name, xlabel="", fontsize="16", label='WP', fontname="times-bold")
        elif 'eicher:Mit' in str(objekt):
            g.attr('node', shape='cylinder', image ='', width='0.6', height= '0.6', fixedsize = 'True')
            g.node(objekt.Name, xlabel=objekt.Name, fontsize="14", label="", fontname="times-bold")
        elif '3-Wege-Ventil' in str(objekt):
            pass
        elif 'T-Stueck' in str(objekt):
            pass
        elif 'Fussbodenheizung' in str(objekt):
            pass
        elif 'Verteiler-Heizkreis' in str(objekt):
            g.attr('node', shape='circle', image = '', width='0.4', height= '0.4', fixedsize = 'True')
            g.node(objekt.Name, xlabel="", fontsize="12", label='Heizkreis')
        elif str(objekt.Name) == 'Frischwasserstation':
            g.attr('node', shape='Mdiamond', image = '', width='0.6', height= '0.6', fixedsize = 'True')
            g.node(objekt.Name, xlabel=objekt.Name, fontsize="14", label="", fontname="times-bold")
        elif 'Rohr -' in str(objekt):
            pass
        else:
            pass
    for verbindung in connections:
        if 'Rohr -' in verbindung.RelatedPort.Nests[0].RelatingObject.Name and verbindung.RelatedPort.Nests[0].RelatedObjects[0].ConnectedTo!= ():
            pass
        elif 'Rohr -' in verbindung.RelatingPort.Nests[0].RelatingObject.Name and verbindung.RelatingPort.Nests[0].RelatedObjects[1].ConnectedFrom!= ():
            if 'Pumpe' in verbindung.RelatingPort.Nests[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.Name or 'Pumpe' in verbindung.RelatedPort.Nests[0].RelatingObject.Name:
                g.edge(verbindung.RelatingPort.Nests[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.Name, verbindung.RelatedPort.Nests[0].RelatingObject.Name, dir='forward', arrowsize='0.5', color="red")
            elif 'Ventil' in verbindung.RelatingPort.Nests[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.Name or 'Ventil' in verbindung.RelatedPort.Nests[0].RelatingObject.Name:
                pass
            elif 'T-Stueck' in verbindung.RelatingPort.Nests[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.Name or 'T-Stueck' in verbindung.RelatedPort.Nests[0].RelatingObject.Name:
                pass
            else:
                g.edge(verbindung.RelatingPort.Nests[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.Name, verbindung.RelatedPort.Nests[0].RelatingObject.Name, dir='forward', arrowsize='0.5', color="blue", fontsize="10")
        else:
            if 'Ruecklauf' in verbindung.RelatingPort.Nests[0].RelatingObject.Name or 'Ruecklauf' in verbindung.RelatedPort.Nests[0].RelatingObject.Name:
                #g.edge(verbindung.RelatingPort.Nests[0].RelatingObject.Name, verbindung.RelatedPort.Nests[0].RelatingObject.Name, dir='forward', arrowsize='0.5', color="blue")   
                pass
            elif 'HK' in verbindung.Name:
                pass
            elif 'Knoten' in verbindung.Name:
                pass
            elif 'Kaltwasser' in verbindung.RelatingPort.Nests[0].RelatingObject.Name:
                g.edge(verbindung.RelatingPort.Nests[0].RelatingObject.Name.split('-')[1], verbindung.RelatedPort.Nests[0].RelatingObject.Name, dir='forward', arrowsize='0.5', color="blue", fontsize="10")
                g.attr('node', shape='circle', image = '', width='0.4', height= '0.4', fixedsize = 'True')
                g.node(verbindung.RelatingPort.Nests[0].RelatingObject.Name.split('-')[1], fontsize="10")
            else:
                g.edge(verbindung.RelatingPort.Nests[0].RelatingObject.Name, verbindung.RelatedPort.Nests[0].RelatingObject.Name.split('-')[1], dir='forward', arrowsize='0.5', color="red", fontsize="10")
                g.attr('node', shape='circle', image = '', width='0.4', height= '0.4', fixedsize = 'True')
                g.node(verbindung.RelatedPort.Nests[0].RelatingObject.Name.split('-')[1], fontsize="10")
    g.render('heizung2', engine = 'neato')

def schema3_fb():
    ifc_file_schema = ifcopenshell.open('System.ifc') 
    connections = ifc_file_schema.by_type("IfcRelConnectsPorts") #IFCRELCONNECTSPORTS
    nests = ifc_file_schema.by_type("IfcRelNests") #IFCRELNESTS
    objekte = []
    for nest in nests:
        objekte.append(nest.RelatingObject)
    g = graphviz.Graph(format='png', filename='heizung3')
    #g = graphviz.Digraph('G', filename='Schema.gv')
    for objekt in objekte:
        if 'Pumpe -' in str(objekt):
            pass
        elif 'Waermepumpe' in str(objekt):
            pass
        elif 'eicher:Mit' in str(objekt):
            pass
        elif '3-Wege-Ventil' in str(objekt):
            g.attr('node', shape='none', image = 'Ventil.png', imagescale='both', width='0.15', height= '0.15', fixedsize = 'True')
            g.node(objekt.Name, xlabel=objekt.Name, fontsize='10', label="")
        elif 'T-Stueck' in str(objekt):
            g.attr('node', shape='none', image = 'T_S.png', imagescale='both', width='0.15', height= '0.15', fixedsize = 'True')
            g.node(objekt.Name, xlabel=objekt.Name, fontsize="10", label="")
        elif 'Fussbodenheizung' in str(objekt):
            objekt.Name = str(objekt.Name).split(' ')[0] + ' ' + str(objekt.Name).split(' ')[1]
            g.attr('node', shape='none', image = 'FB.png', imagescale='both', width='0.6', height= '0.6', fixedsize = 'True')
            g.node(objekt.Name, fontcolor='firebrick1', xlabel=objekt.Name, fontsize="12", label="")
        elif 'Heizkoerper' in str(objekt):
            objekt.Name = str(objekt.Name).split(' ')[0] + ' ' + str(objekt.Name).split(' ')[1]
            g.attr('node', shape='none', image = 'FB.png', imagescale='both', width='0.6', height= '0.6', fixedsize = 'True')
            g.node(objekt.Name, fontcolor='firebrick1', xlabel=objekt.Name, fontsize="12", label="")
        elif 'Verteiler-Heizkreis' in str(objekt):
            g.attr('node', shape='circle', image = '', width='0.5', height= '0.5', fixedsize = 'True')
            g.node(objekt.Name, xlabel=objekt.Name, fontsize="12", label="")
        elif 'Rohr -' in str(objekt):
            pass
    for verbindung in connections:
        if 'Rohr -' in verbindung.RelatedPort.Nests[0].RelatingObject.Name and verbindung.RelatedPort.Nests[0].RelatedObjects[0].ConnectedTo!= ():
            pass
        elif 'Rohr -' in verbindung.RelatingPort.Nests[0].RelatingObject.Name and verbindung.RelatingPort.Nests[0].RelatedObjects[1].ConnectedFrom!= ():
            if 'Pumpe' in verbindung.RelatingPort.Nests[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.Name or 'Pumpe' in verbindung.RelatedPort.Nests[0].RelatingObject.Name:
                pass
            elif 'Waermepumpe' in verbindung.RelatingPort.Nests[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.Name or 'Waermepumpe' in verbindung.RelatedPort.Nests[0].RelatingObject.Name:
                pass
            elif 'eicher:Mit' in verbindung.RelatingPort.Nests[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.Name or 'eicher:Mit' in verbindung.RelatedPort.Nests[0].RelatingObject.Name:
                pass
            elif 'Pufferspeicher' in verbindung.RelatingPort.Nests[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.Name or 'Pufferspeicher' in verbindung.RelatedPort.Nests[0].RelatingObject.Name:
                pass
            elif 'Ventil' in verbindung.RelatingPort.Nests[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.Name or 'Ventil' in verbindung.RelatedPort.Nests[0].RelatingObject.Name:
                g.edge(verbindung.RelatingPort.Nests[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.Name, verbindung.RelatedPort.Nests[0].RelatingObject.Name, dir='forward', arrowsize='0.5', color="red")
            else:
                g.edge(verbindung.RelatingPort.Nests[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.Name, verbindung.RelatedPort.Nests[0].RelatingObject.Name, dir='forward', arrowsize='0.5', color="blue")
        else:
            if 'Ruecklauf' in verbindung.RelatingPort.Nests[0].RelatingObject.Name or 'Ruecklauf' in verbindung.RelatedPort.Nests[0].RelatingObject.Name:
                pass
    g.render('heizung3', engine='neato')

def schema3():
    ifc_file_schema = ifcopenshell.open('System_verbunden.ifc') 
    connections = ifc_file_schema.by_type("IfcRelConnectsPorts") #IFCRELCONNECTSPORTS
    nests = ifc_file_schema.by_type("IfcRelNests") #IFCRELNESTS
    verbindungen = []
    for connection in connections:
        if 'Pumpe' in connection.Name:
            pass
        elif 'Frischwasserstation' in connection.Name:
            pass
        elif 'Puffer' in connection.Name:
            pass
        elif 'TWW-Speicher' in connection.Name:
            pass
        else:
            verbindungen.append(connection)
    objekte = []
    for nest in nests:
        objekte.append(nest.RelatingObject)
    g = graphviz.Graph(format='png', filename='heizung3')
    for objekt in objekte:
        if 'Pumpe -' in str(objekt):
            pass
        elif 'Waermepumpe' in str(objekt):
            pass
        elif 'eicher:Mit' in str(objekt):
            pass
        elif '3-Wege-Ventil' in str(objekt):
            g.attr('node', shape='none', image = 'Ventil.png', imagescale='both', width='0.15', height= '0.15', fixedsize = 'True')
            g.node(objekt.Name, xlabel=objekt.Name, fontsize='10', label="")
        elif 'T-Stueck' in str(objekt):
            pass
        elif 'Fussbodenheizung' in str(objekt):
            objekt.Name = str(objekt.Name).split(' ')[0] + ' ' + str(objekt.Name).split(' ')[1]
            g.attr('node', shape='none', image = 'FB.png', imagescale='both', width='0.6', height= '0.6', fixedsize = 'True')
            g.node(objekt.Name, fontcolor='firebrick1', xlabel=objekt.Name, fontsize="12", label="")
        elif 'Heizkoerper' in str(objekt):
            objekt.Name = str(objekt.Name).split(' ')[0] + ' ' + str(objekt.Name).split(' ')[1]
            g.attr('node', shape='none', image = 'HK.png', imagescale='both', width='0.4', height= '0.4', fixedsize = 'True')
            g.node(objekt.Name, xlabel=objekt.Name, fontsize="12")
        elif 'Verteiler-Heizkreis' in str(objekt):
            g.attr('node', shape='circle', image = '', width='0.6', height= '0.6', fixedsize = 'True')
            g.node(objekt.Name, label='Vorlauf/Ruecklauf HK', fontsize="12")
        elif 'Rohr -' in str(objekt):
            pass
    g.attr('node', shape='none', image = 'T_S.png', imagescale='both', width='0.15', height= '0.15', fixedsize = 'True')
    for verbindung in verbindungen:

        if 'Ruecklauf von' in verbindung.Name and verbindung.RelatedPort.Nests[0].RelatedObjects[0].ConnectedTo!= ():
            g.attr('node', shape='none', image = 'T_S.png', imagescale='both', width='0.15', height= '0.15', fixedsize = 'True', label = "")
            g.node(verbindung.RelatingPort.Nests[0].RelatingObject.Name, label = "")
            if 'T-Stueck' in verbindung.RelatedPort.Nests[0].RelatedObjects[0].ConnectedTo[0].RelatedPort.Nests[0].RelatingObject.Name:
                g.edge(verbindung.RelatingPort.Nests[0].RelatingObject.Name, verbindung.RelatedPort.Nests[0].RelatedObjects[0].ConnectedTo[0].RelatedPort.Nests[0].RelatingObject.Name, dir='forward', arrowsize='0.5', color="blue")
            else:
                g.edge(verbindung.RelatingPort.Nests[0].RelatingObject.Name, verbindung.RelatedPort.Nests[0].RelatedObjects[0].ConnectedTo[0].RelatedPort.Nests[0].RelatingObject.Name, dir='forward', arrowsize='0.5', color="blue")
                g.node(verbindung.RelatingPort.Nests[0].RelatingObject.IsNestedBy[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.IsNestedBy[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.Name, label = "")


        elif 'mit Strang' in verbindung.Name and verbindung.RelatedPort.Nests[0].RelatedObjects[0].ConnectedTo!= ():
            if 'Ruecklauf' in verbindung.Name:
                g.edge(verbindung.RelatingPort.Nests[0].RelatingObject.Name, verbindung.RelatedPort.Nests[0].RelatedObjects[0].ConnectedTo[0].RelatedPort.Nests[0].RelatingObject.Name, dir='forward', arrowsize='0.5', color="blue")
        if 'Vorlauf zu' in verbindung.Name and verbindung.RelatedPort.Nests[0].RelatedObjects[0].ConnectedTo!= ():
            g.attr('node', shape='none', image = 'T_S.png', imagescale='both', width='0.15', height= '0.15', fixedsize = 'True', label = "")
            if 'T-Stueck' in verbindung.RelatingPort.Nests[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.Name:
                g.edge(verbindung.RelatingPort.Nests[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.Name, verbindung.RelatedPort.Nests[0].RelatingObject.Name, dir='forward', arrowsize='0.5', color="red")
            else:
                pass
        elif 'Strang' in verbindung.Name and verbindung.RelatedPort.Nests[0].RelatedObjects[0].ConnectedTo!= ():
            if 'Vorlauf' in verbindung.Name:
                if 'T mit HK' in verbindung.Name:
                    pass
                elif 'mit T' in verbindung.Name:
                    pass
                elif 'Rohre' in verbindung.Name:
                    pass
                else:
                    g.edge(verbindung.RelatingPort.Nests[0].RelatingObject.Name, verbindung.RelatedPort.Nests[0].RelatingObject.IsNestedBy[0].RelatedObjects[0].ConnectedTo[0].RelatedPort.Nests[0].RelatingObject.Name, dir='forward', arrowsize='0.5', color="red")
        elif 'Knoten' in verbindung.Name and verbindung.RelatingPort.Nests[0].RelatedObjects[0].ConnectedTo!= ():
            pass
    g.render('heizung3', engine= 'neato')
    
    
def schema4():
    ifc_file_schema = ifcopenshell.open('System_verbunden.ifc') 
    connections = ifc_file_schema.by_type("IfcRelConnectsPorts") #IFCRELCONNECTSPORTS
    nests = ifc_file_schema.by_type("IfcRelNests") #IFCRELNESTS
    verbindungen = []
    for connection in connections:
        if 'Pumpe' in connection.Name:
            pass
        elif 'Frischwasserstation' in connection.Name:
            pass
        elif 'Puffer' in connection.Name:
            pass
        elif 'TWW-Speicher' in connection.Name:
            pass
        else:
            verbindungen.append(connection)
    objekte = []
    for nest in nests:
        objekte.append(nest.RelatingObject)
    g = graphviz.Graph(format='png', filename='heizung3')
    for objekt in objekte:
        if 'Pumpe -' in str(objekt):
            pass
        elif 'Waermepumpe' in str(objekt):
            pass
        elif 'eicher:Mit' in str(objekt):
            pass
        elif '3-Wege-Ventil' in str(objekt):
            g.attr('node', shape='none', image = 'Ventil.png', imagescale='both', width='0.15', height= '0.15', fixedsize = 'True')
            g.node(objekt.Name, xlabel=objekt.Name, fontsize='10', label="")
        elif 'T-Stueck' in str(objekt):
            pass
        elif 'Fussbodenheizung' in str(objekt):
            objekt.Name = str(objekt.Name).split(' ')[0] + ' ' + str(objekt.Name).split(' ')[1]
            g.attr('node', shape='none', image = 'FB.png', imagescale='both', width='0.6', height= '0.6', fixedsize = 'True')
            g.node(objekt.Name, fontcolor='firebrick1', xlabel=objekt.Name, fontsize="12", label="")
        elif 'Heizkoerper' in str(objekt):
            objekt.Name = str(objekt.Name).split(' ')[0] + ' ' + str(objekt.Name).split(' ')[1]
            g.attr('node', shape='none', image = 'HK.png', imagescale='both', width='0.4', height= '0.4', fixedsize = 'True')
            g.node(objekt.Name, xlabel=objekt.Name, fontsize="12")
        elif 'Verteiler-Heizkreis' in str(objekt):
            g.attr('node', shape='circle', image = '', width='0.6', height= '0.6', fixedsize = 'True')
            g.node(objekt.Name, label='Vorlauf/Ruecklauf HK', fontsize="12")
        elif 'Rohr -' in str(objekt):
            pass
    g.attr('node', shape='none', image = 'T_S.png', imagescale='both', width='0.15', height= '0.15', fixedsize = 'True')
    for verbindung in verbindungen:
        if 'Ruecklauf von' in verbindung.Name and verbindung.RelatedPort.Nests[0].RelatedObjects[0].ConnectedTo!= ():
            g.attr('node', shape='none', image = 'T_S.png', imagescale='both', width='0.15', height= '0.15', fixedsize = 'True', label = "")
            g.node(verbindung.RelatingPort.Nests[0].RelatingObject.Name, label = "")
            if 'T-Stueck' in verbindung.RelatedPort.Nests[0].RelatedObjects[0].ConnectedTo[0].RelatedPort.Nests[0].RelatingObject.Name:
                g.edge(verbindung.RelatingPort.Nests[0].RelatingObject.Name, verbindung.RelatedPort.Nests[0].RelatedObjects[0].ConnectedTo[0].RelatedPort.Nests[0].RelatingObject.Name, dir='forward', arrowsize='0.5', color="blue")
            else:
                g.edge(verbindung.RelatingPort.Nests[0].RelatingObject.Name, verbindung.RelatedPort.Nests[0].RelatedObjects[0].ConnectedTo[0].RelatedPort.Nests[0].RelatingObject.Name, dir='forward', arrowsize='0.5', color="blue")
                g.node(verbindung.RelatingPort.Nests[0].RelatingObject.IsNestedBy[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.IsNestedBy[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.Name, label = "")


        elif 'mit Strang' in verbindung.Name and verbindung.RelatedPort.Nests[0].RelatedObjects[0].ConnectedTo!= ():
            if 'Ruecklauf' in verbindung.Name:
                g.edge(verbindung.RelatingPort.Nests[0].RelatingObject.Name, verbindung.RelatedPort.Nests[0].RelatedObjects[0].ConnectedTo[0].RelatedPort.Nests[0].RelatingObject.Name, dir='forward', arrowsize='0.5', color="blue")
        if 'Vorlauf zu' in verbindung.Name and verbindung.RelatedPort.Nests[0].RelatedObjects[0].ConnectedTo!= ():
            g.attr('node', shape='none', image = 'T_S.png', imagescale='both', width='0.15', height= '0.15', fixedsize = 'True', label = "")
            if 'T-Stueck' in verbindung.RelatingPort.Nests[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.Name:
                g.edge(verbindung.RelatingPort.Nests[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.Name, verbindung.RelatedPort.Nests[0].RelatingObject.Name, dir='forward', arrowsize='0.5', color="red")
            else:
                pass
        elif 'Strang' in verbindung.Name and verbindung.RelatedPort.Nests[0].RelatedObjects[0].ConnectedTo!= ():
            if 'Vorlauf' in verbindung.Name:
                if 'T mit HK' in verbindung.Name:
                    pass
                elif 'mit T' in verbindung.Name:
                    pass
                elif 'Rohre' in verbindung.Name:
                    pass
                elif 'mit K2' in verbindung.Name:
                    pass
                else:
                    g.edge(verbindung.RelatingPort.Nests[0].RelatingObject.Name, verbindung.RelatedPort.Nests[0].RelatingObject.IsNestedBy[0].RelatedObjects[0].ConnectedTo[0].RelatedPort.Nests[0].RelatingObject.Name, dir='forward', arrowsize='0.5', color="red")
        elif 'Knoten3' in verbindung.Name and verbindung.RelatingPort.Nests[0].RelatedObjects[0].ConnectedTo!= ():
            pass
        elif 'Knoten' in verbindung.Name and verbindung.RelatingPort.Nests[0].RelatedObjects[0].ConnectedTo!= ():
            pass
        elif 'mit K' in verbindung.Name:
            pass
    g.render('heizung3', engine= 'fdp')
    
def schema5():
    ifc_file_schema = ifcopenshell.open('System_verbunden.ifc') 
    connections = ifc_file_schema.by_type("IfcRelConnectsPorts") #IFCRELCONNECTSPORTS
    nests = ifc_file_schema.by_type("IfcRelNests") #IFCRELNESTS
    verbindungen = []
    for connection in connections:
        if 'Pumpe' in connection.Name:
            pass
        elif 'Frischwasserstation' in connection.Name:
            pass
        elif 'Puffer' in connection.Name:
            pass
        elif 'TWW-Speicher' in connection.Name:
            pass
        else:
            verbindungen.append(connection)
    objekte = []
    for nest in nests:
        objekte.append(nest.RelatingObject)
    g = graphviz.Graph(format='png', filename='heizung3')
    for objekt in objekte:
        if 'Pumpe -' in str(objekt):
            pass
        elif 'Waermepumpe' in str(objekt):
            pass
        elif 'eicher:Mit' in str(objekt):
            pass
        elif '3-Wege-Ventil' in str(objekt):
            g.attr('node', shape='none', image = 'Ventil.png', imagescale='both', width='0.15', height= '0.15', fixedsize = 'True')
            g.node(objekt.Name, xlabel=objekt.Name, fontsize='10', label="")
        elif 'T-Stueck' in str(objekt):
            pass
        elif 'Fussbodenheizung' in str(objekt):
            objekt.Name = str(objekt.Name).split(' ')[0] + ' ' + str(objekt.Name).split(' ')[1]
            g.attr('node', shape='none', image = 'FB.png', imagescale='both', width='0.6', height= '0.6', fixedsize = 'True')
            g.node(objekt.Name, fontcolor='firebrick1', xlabel=objekt.Name, fontsize="12", label="")
        elif 'Heizkoerper' in str(objekt):
            objekt.Name = str(objekt.Name).split(' ')[0] + ' ' + str(objekt.Name).split(' ')[1]
            g.attr('node', shape='none', image = 'HK.png', imagescale='both', width='0.4', height= '0.4', fixedsize = 'True')
            g.node(objekt.Name, xlabel=objekt.Name, fontsize="12")
        elif 'Verteiler-Heizkreis' in str(objekt):
            g.attr('node', shape='circle', image = '', width='0.6', height= '0.6', fixedsize = 'True')
            g.node(objekt.Name, label='Vorlauf/Ruecklauf HK', fontsize="12")
        elif 'Rohr -' in str(objekt):
            pass
    g.attr('node', shape='none', image = 'T_S.png', imagescale='both', width='0.15', height= '0.15', fixedsize = 'True')
    for verbindung in verbindungen:
        if 'Ruecklauf von' in verbindung.Name and verbindung.RelatedPort.Nests[0].RelatedObjects[0].ConnectedTo!= ():
            g.attr('node', shape='none', image = 'T_S.png', imagescale='both', width='0.15', height= '0.15', fixedsize = 'True', label = "")
            g.node(verbindung.RelatingPort.Nests[0].RelatingObject.Name, label = "")
            if 'T-Stueck' in verbindung.RelatedPort.Nests[0].RelatedObjects[0].ConnectedTo[0].RelatedPort.Nests[0].RelatingObject.Name:
                g.edge(verbindung.RelatingPort.Nests[0].RelatingObject.Name, verbindung.RelatedPort.Nests[0].RelatedObjects[0].ConnectedTo[0].RelatedPort.Nests[0].RelatingObject.Name, dir='forward', arrowsize='0.5', color="blue")
            else:
                g.edge(verbindung.RelatingPort.Nests[0].RelatingObject.Name, verbindung.RelatedPort.Nests[0].RelatedObjects[0].ConnectedTo[0].RelatedPort.Nests[0].RelatingObject.Name, dir='forward', arrowsize='0.5', color="blue")
                g.node(verbindung.RelatingPort.Nests[0].RelatingObject.IsNestedBy[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.IsNestedBy[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.Name, label = "")


        elif 'mit Strang' in verbindung.Name and verbindung.RelatedPort.Nests[0].RelatedObjects[0].ConnectedTo!= ():
            if 'Ruecklauf' in verbindung.Name:
                g.edge(verbindung.RelatingPort.Nests[0].RelatingObject.Name, verbindung.RelatedPort.Nests[0].RelatedObjects[0].ConnectedTo[0].RelatedPort.Nests[0].RelatingObject.Name, dir='forward', arrowsize='0.5', color="blue")
        if 'Vorlauf zu' in verbindung.Name and verbindung.RelatedPort.Nests[0].RelatedObjects[0].ConnectedTo!= ():
            g.attr('node', shape='none', image = 'T_S.png', imagescale='both', width='0.15', height= '0.15', fixedsize = 'True', label = "")
            if 'T-Stueck' in verbindung.RelatingPort.Nests[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.Name:
                if 'Knoten' in verbindung.Name:
                    pass
                else:
                    g.edge(verbindung.RelatingPort.Nests[0].RelatedObjects[1].ConnectedFrom[0].RelatingPort.Nests[0].RelatingObject.Name, verbindung.RelatedPort.Nests[0].RelatingObject.Name, dir='forward', arrowsize='0.5', color="red")
        elif 'Strang' in verbindung.Name and verbindung.RelatedPort.Nests[0].RelatedObjects[0].ConnectedTo!= ():
            if 'Vorlauf' in verbindung.Name:
                if 'T mit HK' in verbindung.Name:
                    pass
                elif 'mit T' in verbindung.Name:
                    pass
                elif 'Rohre' in verbindung.Name:
                    pass
                else:
                    g.edge(verbindung.RelatingPort.Nests[0].RelatingObject.Name, verbindung.RelatedPort.Nests[0].RelatingObject.IsNestedBy[0].RelatedObjects[0].ConnectedTo[0].RelatedPort.Nests[0].RelatingObject.Name, dir='forward', arrowsize='0.5', color="red")
        elif 'Knoten3' in verbindung.Name and verbindung.RelatingPort.Nests[0].RelatedObjects[0].ConnectedTo!= ():
            pass
        elif 'Knoten' in verbindung.Name and verbindung.RelatingPort.Nests[0].RelatedObjects[0].ConnectedTo!= ():
            pass
        elif 'mit K' in verbindung.Name:
            pass
    g.render('heizung3', engine= 'neato')
    
    

# Creates an IfcAxis2Placement3D from Location, Axis and RefDirection specified as Python tuples
def create_ifcaxis2placement(ifcfile, point=O, dir1=Z, dir2=X):
    point = ifcfile.createIfcCartesianPoint(point)
    dir1 = ifcfile.createIfcDirection(dir1)
    dir2 = ifcfile.createIfcDirection(dir2)
    axis2placement = ifcfile.createIfcAxis2Placement3D(point, dir1, dir2)
    return axis2placement

# Creates an IfcLocalPlacement from Location, Axis and RefDirection, specified as Python tuples, and relative placement
def create_ifclocalplacement(ifcfile, point=O, dir1=Z, dir2=X, relative_to=None):
    axis2placement = create_ifcaxis2placement(ifcfile,point,dir1,dir2)
    ifclocalplacement2 = ifcfile.createIfcLocalPlacement(relative_to,axis2placement)
    return ifclocalplacement2

# Creates an IfcPolyLine from a list of points, specified as Python tuples
def create_ifcpolyline(ifcfile, point_list):
    ifcpts = []
    for point in point_list:
        point = ifcfile.createIfcCartesianPoint(point)
        ifcpts.append(point)
    polyline = ifcfile.createIfcPolyLine(ifcpts)
    return polyline

# Creates an IfcExtrudedAreaSolid from a list of points, specified as Python tuples
def create_ifcextrudedareasolid(ifcfile, point_list, ifcaxis2placement, extrude_dir, extrusion):
    polyline = create_ifcpolyline(ifcfile, point_list)
    ifcclosedprofile = ifcfile.createIfcArbitraryClosedProfileDef("AREA", None, polyline)
    ifcdir = ifcfile.createIfcDirection(extrude_dir)
    ifcextrudedareasolid = ifcfile.createIfcExtrudedAreaSolid(ifcclosedprofile, ifcaxis2placement, ifcdir, extrusion)
    return ifcextrudedareasolid

#ID erstellen
create_guid = lambda: ifcopenshell.guid.compress(uuid.uuid1().hex)

# Utility functions
def building_settings(ifc_file, building, location, description, fluctuation, outdoor_temperature, mean_outdoor_temperature):   #kann noch erweitert werden (Adresse, Beispielsweise)
    # IFC hierarchy creation
    building.Name        = description
    building.Description = description
    property_values = [
        ifc_file.createIfcPropertySingleValue("Reference","Reference", ifc_file.create_entity("IfcText", description), None),
        ifc_file.createIfcPropertySingleValue("Location","Location", ifc_file.create_entity("IfcText", location), None),
        ifc_file.createIfcPropertySingleValue("OutsideTemperature", "OutsideTemperature", ifc_file.create_entity("IfcThermodynamicTemperatureMeasure", outdoor_temperature),None),
        ifc_file.createIfcPropertySingleValue("MeanOutsideTemperature", "MeanOutsideTemperature", ifc_file.create_entity("IfcThermodynamicTemperatureMeasure", mean_outdoor_temperature),None),
        ifc_file.createIfcPropertySingleValue("FactorperiodFluctuation", "FactorperiodFluctuation", ifc_file.create_entity("IfcReal", fluctuation),None),
        ifc_file.createIfcPropertySingleValue("TransmissionHeatLosses", "TransmissionHeatLosses", ifc_file.create_entity("IfcPowerMeasure", 0), None),
        ifc_file.createIfcPropertySingleValue("VentilationHeatLosses", "VentilationHeatLosses", ifc_file.create_entity("IfcPowerMeasure", 0), None)
        ]
    property_set = ifc_file.createIfcPropertySet(create_guid(), building.OwnerHistory, "Pset_Building", None, property_values)
    ifc_file.createIfcRelDefinesByProperties(create_guid(), building.OwnerHistory, None, None, [building], property_set)
    
    #Gebäudebauteile
    building_Bauteile= ifc_file.create_entity("IfcRelContainedInSpatialStructure")
    building_Bauteile.GlobalId = ifcopenshell.guid.compress(uuid.uuid1().hex)
    building_Bauteile.OwnerHistory = building.OwnerHistory
    building_Bauteile.Name = "Bauteile zu " + description
    building_Bauteile.RelatedElements = []
    building_Bauteile.RelatingStructure = building

# Utility functions
def trinkwarm_building_neu(ifc_file, building, anzahl_personen, warmwassertemperatur):
    personen = int(anzahl_personen)
    abstand = 10.0
    qmax  = personen*1.45
    if warmwassertemperatur == '':
        warmwassertemperatur = 50.0
    else:
        warmwassertemperatur = float(warmwassertemperatur)
    property_values = [
        ifc_file.createIfcPropertySingleValue("Number_of_people", "Number_of_people", ifc_file.create_entity("IfcReal", personen),None),
        ifc_file.createIfcPropertySingleValue("Hotwatertemperature", "Hotwatertemperature", ifc_file.create_entity("IfcThermodynamicTemperatureMeasure", warmwassertemperatur),None),
        ifc_file.createIfcPropertySingleValue("Timeperiod_between_use", "Timeperiod_between_use", ifc_file.create_entity("IfcReal", abstand),None)
        ]
    property_set = ifc_file.createIfcPropertySet(create_guid(), building.OwnerHistory, "Pset_Residents_TWW", None, property_values)
    ifc_file.createIfcRelDefinesByProperties(create_guid(), building.OwnerHistory, None, None, [building], property_set)
    cw    = 0.001163
    tcw   = 10.0
    trinkwarmwassermenge = qmax/(cw*(warmwassertemperatur-tcw))*1.15
    q_wp       = trinkwarmwassermenge*cw*(warmwassertemperatur-tcw)/abstand
    
    property_values1 = [
        ifc_file.createIfcPropertySingleValue("Needed_Power_TWW", "Needed_Power_TWW", ifc_file.create_entity("IfcPowerMeasure", q_wp),None)
        ]
    property_set1 = ifc_file.createIfcPropertySet(create_guid(), building.OwnerHistory, "TWW_Quantities", None, property_values1)
    ifc_file.createIfcRelDefinesByProperties(create_guid(), building.OwnerHistory, None, None, [building], property_set1)

def trinkwarm_building(ifc_file, building, anzahl_personen, temperatur_soll):   #kann noch erweitert werden (Adresse, Beispielsweise)
    personen = int(anzahl_personen)
    qmax  = personen*1.45
    if temperatur_soll == '':
        temp = 60.0
    else:
        temp = float(temperatur_soll)
    property_values = [
        ifc_file.createIfcPropertySingleValue("Number_of_people", "Number_of_people", ifc_file.create_entity("IfcReal", personen),None),
        ifc_file.createIfcPropertySingleValue("Storage_temperature", "Storage_temperature", ifc_file.create_entity("IfcThermodynamicTemperatureMeasure", temp),None),
        ifc_file.createIfcPropertySingleValue("Timeperiod_between_use", "Timeperiod_between_use", ifc_file.create_entity("IfcReal", 12.0),None)
        ]
    property_set = ifc_file.createIfcPropertySet(create_guid(), building.OwnerHistory, "Pset_Residents_TWW", None, property_values)
    ifc_file.createIfcRelDefinesByProperties(create_guid(), building.OwnerHistory, None, None, [building], property_set)
    cw    = 0.001163
    tcw   = 10.0
    v_tww = qmax/(cw*(temp-tcw))*1.15
    property_values1 = [
        ifc_file.createIfcPropertySingleValue("Needed_Power_TWW", "Needed_Power_TWW", ifc_file.create_entity("IfcPowerMeasure", 0.0),None),
        ifc_file.createIfcPropertySingleValue("Real_Storage_Size", "Real_Storage_Size", ifc_file.create_entity("IfcVolumeMeasure", v_tww/1000), None),
        ifc_file.createIfcPropertySingleValue("Ideal_Storage_Size", "Ideal_Storage_Size", ifc_file.create_entity("IfcVolumeMeasure", v_tww/1000), None)
        ]
    property_set1 = ifc_file.createIfcPropertySet(create_guid(), building.OwnerHistory, "TWW_Quantities", None, property_values1)
    ifc_file.createIfcRelDefinesByProperties(create_guid(), building.OwnerHistory, None, None, [building], property_set1)

def trinkwarm_building2(ifc_file, building, speichergröße):
    if speichergröße == '':
        speicher  = building.IsDefinedBy[1].RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue
    else:
        speicher  = float(speichergröße)/1000
    abstand = 10
    cw         = 0.001163
    tcw        = 10.0
    t_speicher = building.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[1].NominalValue.wrappedValue
    
    q_wp       = speicher*1000*cw*(t_speicher-tcw)/abstand
    building.IsDefinedBy[1].RelatingPropertyDefinition.HasProperties[1].NominalValue.wrappedValue = speicher
    building.IsDefinedBy[1].RelatingPropertyDefinition.HasProperties[0].NominalValue.wrappedValue = q_wp

#Raum erstellen
def add_room(ifc_file, building, name, height, area, t_room, nmin):
    #Raum
    context = ifc_file.by_type("IfcGeometricRepresentationContext")[0]
    room_placement = create_ifclocalplacement(ifc_file)
    polyline = create_ifcpolyline(ifc_file, [(0.0, 0.0, 0.0), (50.0, 0.0, 0.0)])
    axis_representation = ifc_file.createIfcShapeRepresentation(context, "Axis", "Curve2D", [polyline])
    extrusion_placement = create_ifcaxis2placement(ifc_file, (0.0, 0.0, 0.0), (0.0, 0.0, 10.0), (10.0, 0.0, 0.0))
    point_list_extrusion_area = [(0.0, -10.0, 0.0), (50.0, -10.0, 0.0), (50.0, 10.0, 0.0), (0.0, 10.0, 0.0), (0.0, -10.0, 0.0)]
    solid = create_ifcextrudedareasolid(ifc_file, point_list_extrusion_area, extrusion_placement, (0.0, 0.0, 10.0), 30.0)
    body_representation = ifc_file.createIfcShapeRepresentation(context, "Body", "SweptSolid", [solid])
    product_shape = ifc_file.createIfcProductDefinitionShape(None, None, [axis_representation, body_representation])
    room = ifc_file.createIfcSpace(create_guid(), building.OwnerHistory, name, 'Raum: ' + name, None, room_placement, product_shape, None)

    #Property_set
    property_values = [
        ifc_file.createIfcPropertySingleValue("Reference","Reference", ifc_file.create_entity("IfcText", 'Raum: ' + name), None),
        ifc_file.createIfcPropertySingleValue("IntValue","IntValue", ifc_file.create_entity("IfcInteger", 2), None),
        ifc_file.createIfcPropertySingleValue("TransmissionHeatLosses", "TransmissionHeatLosses", ifc_file.create_entity("IfcPowerMeasure", 0), None),
        ifc_file.createIfcPropertySingleValue("VentilationHeatLosses", "VentilationHeatLosses", ifc_file.create_entity("IfcPowerMeasure", 0), None),
        ifc_file.createIfcPropertySingleValue("SetTemperature", "SetTemperature", ifc_file.create_entity("IfcThermodynamicTemperatureMeasure", t_room),None),
        ifc_file.createIfcPropertySingleValue("MinimumAirExchangeRate", "MinimumAirExchangeRate", ifc_file.create_entity("IfcCountMeasure", nmin), None)
        ]
    property_set = ifc_file.createIfcPropertySet(create_guid(), building.OwnerHistory, "Pset_Space", None, property_values)
    ifc_file.createIfcRelDefinesByProperties(create_guid(), building.OwnerHistory, None, None, [room], property_set)
    #Quantities
    quantity_values = [
        ifc_file.createIfcQuantityLength("Hight", "Hight of the room", None, height*1000),
        ifc_file.createIfcQuantityArea("Area", "Area of the room", None, area),
        ifc_file.createIfcQuantityVolume("Volume", "Volume of the room", None, height*area)
        ]
    element_quantity = ifc_file.createIfcElementQuantity(create_guid(), building.OwnerHistory, "BaseQuantities", None, None, quantity_values)
    ifc_file.createIfcRelDefinesByProperties(create_guid(), building.OwnerHistory, None, None, [room], element_quantity)
    #Raumbauteile
    room_Bauteile= ifc_file.create_entity("IfcRelContainedInSpatialStructure")
    room_Bauteile.GlobalId = ifcopenshell.guid.compress(uuid.uuid1().hex)
    room_Bauteile.OwnerHistory = building.OwnerHistory
    room_Bauteile.Name = "Bauteile zu " + name
    room_Bauteile.RelatedElements = []
    room_Bauteile.RelatingStructure = room
    #Gebäude mit Raum
    building.ContainsElements[0].RelatedElements = building.ContainsElements[0].RelatedElements + (room,)
    #Lueftungswaermeverlust
    nmin             = room.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[5].NominalValue.wrappedValue
    t_outside_a      = building.IsDefinedBy[0]
    t_outside        = t_outside_a.RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue
    roomvolume       = room.IsDefinedBy[1].RelatingPropertyDefinition.Quantities[2].VolumeValue
    t_room           = room.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue
    room.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[3].NominalValue.wrappedValue = round(nmin*roomvolume*0.34*(t_room-t_outside),4)
    building.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[6].NominalValue.wrappedValue = building.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[6].NominalValue.wrappedValue + 0.5*room.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[3].NominalValue.wrappedValue
def add_wall(ifc_file, building, room, description, length, height, thickness, u_value, boundary, tangrenz):
    #Wand
    # Wall creation: Define the wall shape as a polyline axis and an extruded area solid
    context = ifc_file.by_type("IfcGeometricRepresentationContext")[0]
    wall_placement = create_ifclocalplacement(ifc_file)
    polyline = create_ifcpolyline(ifc_file, [(0.0, 0.0, 0.0), (50.0, 0.0, 0.0)])
    axis_representation = ifc_file.createIfcShapeRepresentation(context, "Axis", "Curve2D", [polyline])
    extrusion_placement = create_ifcaxis2placement(ifc_file, (0.0, 0.0, 0.0), (0.0, 0.0, 10.0), (10.0, 0.0, 0.0))
    point_list_extrusion_area = [(0.0, -10.0, 0.0), (50.0, -10.0, 0.0), (50.0, 10.0, 0.0), (0.0, 10.0, 0.0), (0.0, -10.0, 0.0)]
    solid = create_ifcextrudedareasolid(ifc_file, point_list_extrusion_area, extrusion_placement, (0.0, 0.0, 10.0), 30.0)
    body_representation = ifc_file.createIfcShapeRepresentation(context, "Body", "SweptSolid", [solid])
    product_shape = ifc_file.createIfcProductDefinitionShape(None, None, [axis_representation, body_representation])
    wall = ifc_file.createIfcWallStandardCase(create_guid(), building.OwnerHistory, description, boundary, None, wall_placement, product_shape, None)
    # Create and assign property set
    #Property_set
    property_values = [
        ifc_file.createIfcPropertySingleValue("Reference","Reference", ifc_file.create_entity("IfcText", description), None),
        ifc_file.createIfcPropertySingleValue("IsExternal","IsExternal", ifc_file.create_entity("IfcBoolean", boundary == "e" ), None),
        ifc_file.createIfcPropertySingleValue("ThermalTransmittance","Thermaltransmittance", ifc_file.create_entity("IfcReal", u_value), None),
        ifc_file.createIfcPropertySingleValue("IntValue","IntValue", ifc_file.create_entity("IfcInteger", 2), None),
        ifc_file.createIfcPropertySingleValue("TransmissionHeatLosses", "TransmissionHeatLosses", ifc_file.create_entity("IfcPowerMeasure", 0), None)
        ]
    property_set = ifc_file.createIfcPropertySet(create_guid(), building.OwnerHistory, "Pset_Wall", None, property_values)
    ifc_file.createIfcRelDefinesByProperties(create_guid(), building.OwnerHistory, None, None, [wall], property_set)
    #Quantities
    quantity_values = [
        ifc_file.createIfcQuantityLength("Length", "Length of the wall", None, length*1000),
        ifc_file.createIfcQuantityLength("Hight", "Hight of the wall", None, height*1000),
        ifc_file.createIfcQuantityArea("Area", "Area of the wall", None, length*height),
        ifc_file.createIfcQuantityLength("Thickness", "Thickness of the wall", None, thickness*10)
        ]
    element_quantity = ifc_file.createIfcElementQuantity(create_guid(), building.OwnerHistory, "BaseQuantities", None, None, quantity_values)
    ifc_file.createIfcRelDefinesByProperties(create_guid(), building.OwnerHistory, None, None, [wall], element_quantity)
    #Raum mit Wand
    room.ContainsElements[0].RelatedElements = room.ContainsElements[0].RelatedElements + (wall,)
    #Transmissionswärmeverluste des Bauteils
    t_outside        = building.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue
    wall_area         = wall.IsDefinedBy[1].RelatingPropertyDefinition.Quantities[2].AreaValue
    u_wall           = wall.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue
    t_room           = room.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue
    if boundary== "e":
        wall.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue = round(wall_area*u_wall*(t_room-t_outside),2)
        building.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[5].NominalValue.wrappedValue = building.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[5].NominalValue.wrappedValue + wall.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue
    if boundary== "b":
        wall.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue = round(wall_area*u_wall*(t_room-tangrenz),2)
    if boundary== "u":
        wall.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue = round(wall_area*u_wall*(t_room-tangrenz),2)
    room.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue = room.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue + wall.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue
def add_window(ifc_file, building, room, wall, description, wide, height, u_value, boundary, tangrenz):
    #Fenster
    # Create and associate an opening for the window in the wall
    context = ifc_file.by_type("IfcGeometricRepresentationContext")[0]
    wall_placement = wall.ObjectPlacement
    opening_placement = create_ifclocalplacement(ifc_file, (0.5, 0.0, 1.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0), wall_placement)
    opening_extrusion_placement = create_ifcaxis2placement(ifc_file, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))
    point_list_opening_extrusion_area = [(0.0, -0.1, 0.0), (3.0, -0.1, 0.0), (3.0, 0.1, 0.0), (0.0, 0.1, 0.0), (0.0, -0.1, 0.0)]
    opening_solid = create_ifcextrudedareasolid(ifc_file, point_list_opening_extrusion_area, opening_extrusion_placement, (0.0, 0.0, 1.0), 1.0)
    opening_representation = ifc_file.createIfcShapeRepresentation(context, "Body", "SweptSolid", [opening_solid])
    opening_shape = ifc_file.createIfcProductDefinitionShape(None, None, [opening_representation])
    opening_element = ifc_file.createIfcOpeningElement(create_guid(), building.OwnerHistory, "Oeffnung zu "+wall.Name,"Oeffnung zu " +description, None, opening_placement, opening_shape, None)
    ifc_file.createIfcRelVoidsElement(create_guid(), building.OwnerHistory, None, None, wall, opening_element)
    # Create a simplified representation for the Window
    window_placement = create_ifclocalplacement(ifc_file, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0), wall_placement)
    window_extrusion_placement = create_ifcaxis2placement(ifc_file, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))
    point_list_window_extrusion_area = [(0.0, -0.01, 0.0), (3.0, -0.01, 0.0), (3.0, 0.01, 0.0), (0.0, 0.01, 0.0), (0.0, -0.01, 0.0)]
    window_solid = create_ifcextrudedareasolid(ifc_file, point_list_window_extrusion_area, window_extrusion_placement, (0.0, 0.0, 1.0), 1.0)
    window_representation = ifc_file.createIfcShapeRepresentation(context, "Body", "SweptSolid", [window_solid])
    window_shape = ifc_file.createIfcProductDefinitionShape(None, None, [window_representation])
    window = ifc_file.createIfcWindow(create_guid(), building.OwnerHistory, "Fenster zu " +wall.Name, description, None, window_placement, window_shape, None, None)
    # Relate the window to the opening element
    ifc_file.createIfcRelFillsElement(create_guid(), building.OwnerHistory, None, None, opening_element, window)
    #Property_set
    property_values = [
        ifc_file.createIfcPropertySingleValue("Reference","Reference", ifc_file.create_entity("IfcText", description), None),
        ifc_file.createIfcPropertySingleValue("IsExternal","IsExternal", ifc_file.create_entity("IfcBoolean", boundary == "e" ), None),
        ifc_file.createIfcPropertySingleValue("ThermalTransmittance","Thermaltransmittance", ifc_file.create_entity("IfcReal", u_value), None),
        ifc_file.createIfcPropertySingleValue("IntValue","IntValue", ifc_file.create_entity("IfcInteger", 2), None),
        ifc_file.createIfcPropertySingleValue("TransmissionHeatLosses", "TransmissionHeatLosses", ifc_file.create_entity("IfcPowerMeasure", 0), None)
        ]
    property_set = ifc_file.createIfcPropertySet(create_guid(), building.OwnerHistory, "Pset_Window", None, property_values)
    ifc_file.createIfcRelDefinesByProperties(create_guid(), building.OwnerHistory, None, None, [window], property_set)
    #Quantities
    quantity_values = [
        ifc_file.createIfcQuantityLength("Wide", "Wide of the window", None, wide*1000),
        ifc_file.createIfcQuantityLength("Hight", "Hight of the window", None, height*1000),
        ifc_file.createIfcQuantityArea("Area", "Area of the window", None, wide*height)
        ]
    element_quantity = ifc_file.createIfcElementQuantity(create_guid(), building.OwnerHistory, "BaseQuantities", None, None, quantity_values)
    ifc_file.createIfcRelDefinesByProperties(create_guid(), building.OwnerHistory, None, None, [window], element_quantity)
    #Raum mit Fenster
    room.ContainsElements[0].RelatedElements = room.ContainsElements[0].RelatedElements + (window,)
    #Parameter
    u_wall           = wall.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue
    t_outside        = building.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue
    t_room           = room.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue
    window_area      = window.IsDefinedBy[1].RelatingPropertyDefinition.Quantities[2].AreaValue
    u_window         = window.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue
    #Korrektur Transmissionswärmeverluste Wand und Raum > Abzüge von Wandberechnung durch Fensterfläche
    if boundary== "e":
        wall_deduction = round(window_area*u_wall*(t_room-t_outside),2)
    if boundary== "b":
        wall_deduction = round(window_area*u_wall*(t_room-t_room),2)
    if boundary== "u":
        wall_deduction = round(window_area*u_wall*(0.5),2)
    wall.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue = wall.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue - wall_deduction
    room.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue = room.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue - wall_deduction
    #Transmissionswärmeverluste des Bauteils
    if boundary== "e":
        window.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue = round(window_area*u_window*(t_room-t_outside),2)
        building.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[5].NominalValue.wrappedValue = building.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[5].NominalValue.wrappedValue - wall_deduction
        building.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[5].NominalValue.wrappedValue = building.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[5].NominalValue.wrappedValue + window.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue
    if boundary== "b":
        window.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue = round(window_area*u_window*(t_room-tangrenz),2)
    if boundary== "u":
        window.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue = round(window_area*u_window*(t_room-tangrenz),2)
    room.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue = room.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue + window.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue
def add_door(ifc_file, building, room, wall, description, wide, height, u_value, boundary, tangrenz):
    #Door 
    context = ifc_file.by_type("IfcGeometricRepresentationContext")[0]
    wall_placement = wall.ObjectPlacement
    opening_placement = create_ifclocalplacement(ifc_file, (0.5, 0.0, 1.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0), wall_placement)
    opening_extrusion_placement = create_ifcaxis2placement(ifc_file, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))
    point_list_opening_extrusion_area = [(0.0, -0.1, 0.0), (3.0, -0.1, 0.0), (3.0, 0.1, 0.0), (0.0, 0.1, 0.0), (0.0, -0.1, 0.0)]
    opening_solid = create_ifcextrudedareasolid(ifc_file, point_list_opening_extrusion_area, opening_extrusion_placement, (0.0, 0.0, 1.0), 1.0)
    opening_representation = ifc_file.createIfcShapeRepresentation(context, "Body", "SweptSolid", [opening_solid])
    opening_shape = ifc_file.createIfcProductDefinitionShape(None, None, [opening_representation])
    opening_element = ifc_file.createIfcOpeningElement(create_guid(), building.OwnerHistory, "Oeffnung zu "+wall.Name, "Oeffnung zu " +description, None, opening_placement, opening_shape, None)
    ifc_file.createIfcRelVoidsElement(create_guid(), building.OwnerHistory, None, None, wall, opening_element)
    # Create a simplified representation for the Window
    door_placement = create_ifclocalplacement(ifc_file, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0), wall_placement)
    door_extrusion_placement = create_ifcaxis2placement(ifc_file, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))
    point_list_door_extrusion_area = [(0.0, -0.01, 0.0), (3.0, -0.01, 0.0), (3.0, 0.01, 0.0), (0.0, 0.01, 0.0), (0.0, -0.01, 0.0)]
    door_solid = create_ifcextrudedareasolid(ifc_file, point_list_door_extrusion_area, door_extrusion_placement, (0.0, 0.0, 1.0), 1.0)
    door_representation = ifc_file.createIfcShapeRepresentation(context, "Body", "SweptSolid", [door_solid])
    door_shape = ifc_file.createIfcProductDefinitionShape(None, None, [door_representation])
    door = ifc_file.createIfcDoor(create_guid(), building.OwnerHistory, "Tuer zu " +wall.Name, description, None, door_placement, door_shape, None, None)
    # Relate the window to the opening element
    ifc_file.createIfcRelFillsElement(create_guid(), building.OwnerHistory, None, None, opening_element, door)
    #Property_set
    property_values = [
        ifc_file.createIfcPropertySingleValue("Reference","Reference", ifc_file.create_entity("IfcText", description), None),
        ifc_file.createIfcPropertySingleValue("IsExternal","IsExternal", ifc_file.create_entity("IfcBoolean", boundary == "e" ), None),
        ifc_file.createIfcPropertySingleValue("ThermalTransmittance","Thermaltransmittance", ifc_file.create_entity("IfcReal", u_value), None),
        ifc_file.createIfcPropertySingleValue("IntValue","IntValue", ifc_file.create_entity("IfcInteger", 2), None),
        ifc_file.createIfcPropertySingleValue("TransmissionHeatLosses", "TransmissionHeatLosses", ifc_file.create_entity("IfcPowerMeasure", 0), None)
        ]
    property_set = ifc_file.createIfcPropertySet(create_guid(), building.OwnerHistory, "Pset_Door", None, property_values)
    ifc_file.createIfcRelDefinesByProperties(create_guid(), building.OwnerHistory, None, None, [door], property_set)
    #Quantities
    quantity_values = [
        ifc_file.createIfcQuantityLength("Wide", "Wide of the door", None, wide*1000),
        ifc_file.createIfcQuantityLength("Hight", "Hight of the door", None, height*1000),
        ifc_file.createIfcQuantityArea("Area", "Area of the door", None, wide*height)
        ]
    element_quantity = ifc_file.createIfcElementQuantity(create_guid(), building.OwnerHistory, "BaseQuantities", None, None, quantity_values)
    ifc_file.createIfcRelDefinesByProperties(create_guid(), building.OwnerHistory, None, None, [door], element_quantity)
    #Raum mit Fenster
    room.ContainsElements[0].RelatedElements = room.ContainsElements[0].RelatedElements + (door,)
    #Parameter
    u_wall           = wall.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue
    t_outside        = building.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue
    t_room           = room.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue
    door_area        = door.IsDefinedBy[1].RelatingPropertyDefinition.Quantities[2].AreaValue
    u_door           = door.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue
    #Korrektur Transmissionswärmeverluste Wand und Raum > Abzüge von Wandberechnung durch Fensterfläche
    if boundary== "e":
        wall_deduction = round(door_area*u_wall*(t_room-t_outside),2)
    if boundary== "b":
        wall_deduction = round(door_area*u_wall*(t_room-t_room),2)
    if boundary== "u":
        wall_deduction = round(door_area*u_wall*(0.5),2)
    wall.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue = wall.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue - wall_deduction
    room.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue = room.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue - wall_deduction
    #Transmissionswärmeverluste des Bauteils
    if boundary== "e":
        door.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue = round(door_area*u_door*(t_room-t_outside),2)
        building.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[5].NominalValue.wrappedValue = building.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[5].NominalValue.wrappedValue - wall_deduction
        building.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[5].NominalValue.wrappedValue = building.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[5].NominalValue.wrappedValue + door.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue
    if boundary== "b":
        door.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue = round(door_area*u_door*(t_room-tangrenz),2)
    if boundary== "u":
        door.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue = round(door_area*u_door*(t_room-tangrenz),2)
    room.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue = room.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue + door.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue

def add_floor(ifc_file, building, room, description, area, thickness, u_value, boundary, tangrenz):
    #Boden
    context = ifc_file.by_type("IfcGeometricRepresentationContext")[0]
    floor_placement = create_ifclocalplacement(ifc_file)
    polyline = create_ifcpolyline(ifc_file, [(0.0, 0.0, 0.0), (50.0, 0.0, 0.0)])
    axis_representation = ifc_file.createIfcShapeRepresentation(context, "Axis", "Curve2D", [polyline])
    extrusion_placement = create_ifcaxis2placement(ifc_file, (0.0, 0.0, 0.0), (0.0, 0.0, 10.0), (10.0, 0.0, 0.0))
    point_list_extrusion_area = [(0.0, -10.0, 0.0), (50.0, -10.0, 0.0), (50.0, 10.0, 0.0), (0.0, 10.0, 0.0), (0.0, -10.0, 0.0)]
    solid = create_ifcextrudedareasolid(ifc_file, point_list_extrusion_area, extrusion_placement, (0.0, 0.0, 10.0), 30.0)
    body_representation = ifc_file.createIfcShapeRepresentation(context, "Body", "SweptSolid", [solid])
    product_shape = ifc_file.createIfcProductDefinitionShape(None, None, [axis_representation, body_representation])
    floor = ifc_file.createIfcSlab(create_guid(), building.OwnerHistory, description, boundary, None, floor_placement, product_shape, None)
    #Property_set
    property_values = [
        ifc_file.createIfcPropertySingleValue("Reference","Reference", ifc_file.create_entity("IfcText", description), None),
        ifc_file.createIfcPropertySingleValue("IsExternal","IsExternal", ifc_file.create_entity("IfcBoolean", boundary == "e" ), None),
        ifc_file.createIfcPropertySingleValue("ThermalTransmittance","Thermaltransmittance", ifc_file.create_entity("IfcReal", u_value), None),
        ifc_file.createIfcPropertySingleValue("IntValue","IntValue", ifc_file.create_entity("IfcInteger", 2), None),
        ifc_file.createIfcPropertySingleValue("TransmissionHeatLosses", "TransmissionHeatLosses", ifc_file.create_entity("IfcPowerMeasure", 0), None)
        ]
    property_set = ifc_file.createIfcPropertySet(create_guid(), building.OwnerHistory, "Pset_Floor", None, property_values)
    ifc_file.createIfcRelDefinesByProperties(create_guid(), building.OwnerHistory, None, None, [floor], property_set)
    #Quantities
    quantity_values = [
        ifc_file.createIfcQuantityArea("Area", "Area of the floor", None, area),
        ifc_file.createIfcQuantityLength("Thickness", "Thickness of the floor", None, thickness*10)
        ]
    element_quantity = ifc_file.createIfcElementQuantity(create_guid(), building.OwnerHistory, "BaseQuantities", None, None, quantity_values)
    ifc_file.createIfcRelDefinesByProperties(create_guid(), building.OwnerHistory, None, None, [floor], element_quantity)
    #Raum mit Boden
    room.ContainsElements[0].RelatedElements = room.ContainsElements[0].RelatedElements + (floor,)
    #Transmissionswärmeverluste des Bauteils
    t_outside        = building.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue
    t_room           = room.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue
    t_outside_mean   = building.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[3].NominalValue.wrappedValue
    fg1              = building.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue
    fg2              = (t_room - t_outside_mean)/(t_room - t_outside)
    floor_area       = floor.IsDefinedBy[1].RelatingPropertyDefinition.Quantities[0].AreaValue
    u_floor          = floor.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue

    if boundary== "g": #Erdreich
        floor.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue = round((fg1*fg2*floor_area*u_floor),2)
        building.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[5].NominalValue.wrappedValue = building.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[5].NominalValue.wrappedValue + floor.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue
    if boundary== "u":    #u= unbeheizt
        floor.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue = round(floor_area*u_floor*(t_room-tangrenz),2)
    if boundary== "b":
        floor.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue = round(floor_area*u_floor*(t_room-tangrenz),2)
    room.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue = room.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue + floor.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue

def add_ceiling(ifc_file, building, room, description, area, thickness, u_value, boundary, tangrenz):
    #Decke
    #Boden
    context = ifc_file.by_type("IfcGeometricRepresentationContext")[0]
    ceiling_placement = create_ifclocalplacement(ifc_file)
    polyline = create_ifcpolyline(ifc_file, [(0.0, 0.0, 0.0), (50.0, 0.0, 0.0)])
    axis_representation = ifc_file.createIfcShapeRepresentation(context, "Axis", "Curve2D", [polyline])
    extrusion_placement = create_ifcaxis2placement(ifc_file, (0.0, 0.0, 0.0), (0.0, 0.0, 10.0), (10.0, 0.0, 0.0))
    point_list_extrusion_area = [(0.0, -10.0, 0.0), (50.0, -10.0, 0.0), (50.0, 10.0, 0.0), (0.0, 10.0, 0.0), (0.0, -10.0, 0.0)]
    solid = create_ifcextrudedareasolid(ifc_file, point_list_extrusion_area, extrusion_placement, (0.0, 0.0, 10.0), 30.0)
    body_representation = ifc_file.createIfcShapeRepresentation(context, "Body", "SweptSolid", [solid])
    product_shape = ifc_file.createIfcProductDefinitionShape(None, None, [axis_representation, body_representation])
    ceiling = ifc_file.createIfcSlab(create_guid(), building.OwnerHistory, description, boundary, None, ceiling_placement, product_shape, None)
    #Property_set
    property_values = [
        ifc_file.createIfcPropertySingleValue("Reference","Reference", ifc_file.create_entity("IfcText", description), None),
        ifc_file.createIfcPropertySingleValue("IsExternal","IsExternal", ifc_file.create_entity("IfcBoolean", boundary == "e" ), None),
        ifc_file.createIfcPropertySingleValue("ThermalTransmittance","Thermaltransmittance", ifc_file.create_entity("IfcReal", u_value), None),
        ifc_file.createIfcPropertySingleValue("IntValue","IntValue", ifc_file.create_entity("IfcInteger", 2), None),
        ifc_file.createIfcPropertySingleValue("TransmissionHeatLosses", "TransmissionHeatLosses", ifc_file.create_entity("IfcPowerMeasure", 0), None)
        ]
    property_set = ifc_file.createIfcPropertySet(create_guid(), building.OwnerHistory, "Pset_Ceiling", None, property_values)
    ifc_file.createIfcRelDefinesByProperties(create_guid(), building.OwnerHistory, None, None, [ceiling], property_set)
    #Quantities
    quantity_values = [
        ifc_file.createIfcQuantityArea("Area", "Area of the ceiling", None, area),
        ifc_file.createIfcQuantityLength("Thickness", "Thickness of the ceiling", None, thickness*10)
        ]
    element_quantity = ifc_file.createIfcElementQuantity(create_guid(), building.OwnerHistory, "BaseQuantities", None, None, quantity_values)
    ifc_file.createIfcRelDefinesByProperties(create_guid(), building.OwnerHistory, None, None, [ceiling], element_quantity)
    #Raum mit Decke
    room.ContainsElements[0].RelatedElements = room.ContainsElements[0].RelatedElements + (ceiling,)
    #Transmissionswärmeverluste des Bauteils
    t_outside        = building.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue
    t_room           = room.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue
    ceiling_area     = ceiling.IsDefinedBy[1].RelatingPropertyDefinition.Quantities[0].AreaValue
    u_ceiling        = ceiling.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue

    if boundary== "e":
        ceiling.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue = round(ceiling_area*u_ceiling*(t_room-t_outside),2)
        building.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[5].NominalValue.wrappedValue = building.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[5].NominalValue.wrappedValue + ceiling.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue
    if boundary== "b":
        ceiling.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue = round(ceiling_area*u_ceiling*(t_room-tangrenz),2)
    if boundary== "u":
        ceiling.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue = round(ceiling_area*u_ceiling*(t_room-tangrenz),2)
    room.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue = room.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[2].NominalValue.wrappedValue + ceiling.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[4].NominalValue.wrappedValue




def colebrook_prandtl(epsilon, D, Re):
    moody = 5.5*1e-3+0.15*(epsilon/D)**(1/3)
    #print(moody)
    # Initialisieren Sie einen Anfangswert für f
    f = 0.02
    # Toleranz für die Genauigkeit der Berechnung
    tol = 1e-6
    # Maximale Anzahl von Iterationen
    max_iter = 150
    
    for i in range(max_iter):
        # Den rechten Teil der Prandtl-Colebrook-Formel berechnen
        #right = -2.0 * math.log10((epsilon / D) / 3.7 + 2.51 / (Re * math.sqrt(f)))
        right = 1 / (2.0 * math.log10((2.51 / (Re * math.sqrt(f))) + (0.27 * epsilon / D)))**2
        # Neuen Wert für f berechnen
        f_new = right
        
        # Überprüfen, ob die Änderung von f klein genug ist
        if abs(f_new - f) < tol * f_new:
            return f_new
        f = f_new

    return None
def darcy_weisbach(L, rho, V, D, f):
    rohrreibungswiderstand = (f*rho*(V**2))/(D*2)    #Pa/m
    delta_P = rohrreibungswiderstand*L
    return delta_P


