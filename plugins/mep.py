#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from urllib.request import urlopen
import xml.etree.ElementTree as ET
import datetime

from unidecode import unidecode

class MEP:
    
    EURO_GROUPS = {
        'Group of the European People\'s Party (Christian Democrats)': 'EPP',
        'Europe of Freedom and Direct Democracy Group': 'EFDD',
        'Group of the Progressive Alliance of Socialists and Democrats in the European Parliament': 'S&D',
        'Confederal Group of the European United Left - Nordic Green Left': 'GUE/NGL',
        'Group of the Greens/European Free Alliance': 'Verts/ALE',
        'Group of the Alliance of Liberals and Democrats for Europe': 'ALDE',
        'Europe of Nations and Freedom Group': 'ENF',
        'European Conservatives and Reformists Group': 'ECR',
        'Non-attached Members': 'N/A'
        }
    
    def __init__(self, xml):
        
        self.full_name = xml.find('fullName').text
        self.country = xml.find('country').text
        self.euro_group = xml.find('politicalGroup').text
        self.mep_id = xml.find('id').text
        self.national_group = xml.find('nationalPoliticalGroup').text
        
        self.euro_group_abbr = self.EURO_GROUPS.get(self.euro_group)
        self.full_name_ascii = unidecode(self.full_name)

class MEPList:
    
    def __init__(self, xml):
        
        self.meps = []
        for mep_elem in xml:
            self.meps.append(MEP(mep_elem))
    
    def search_mep_by_name(self, name):
        ascii_name = unidecode(name).lower()
        results = []
        for mep in self.meps:
            if ascii_name in mep.full_name_ascii.lower():
                results.append(mep)
        return results

class Plugin:
    
    XML_URL = ('http://www.europarl.europa.eu/meps/en/xml.html'
                '?query=full&filter=all')
    
    def __init__(self, bot, handler):
        self.bot = bot
        self.conn = bot.conn
        self.handler = handler
        self.mep_data, self.xml_date = self.get_mep_data(from_web=True)
        self.hooks = [
            {'type': 'command', 'key': '!mep', 'func': self.mep}
        ]
    
    def mep(self, data):
        mep_name = ' '.join(data.trailing).strip()
        if not mep_name:
            self.conn.say('Syntax is "!mep <MEP name>".', data.to)
            return
        results = self.mep_data.search_mep_by_name(mep_name)
        if not results:
            response = 'Sorry, no MEP found for {}.'.format(mep_name)
        elif len(results) == 1:
            mep = results[0]
            response = ('{}, MEP for {}. Euro group: {}. '
                        'National group: {}.'.format(mep.full_name,
                        mep.country, mep.euro_group_abbr, mep.national_group))
        elif len(results) == 2:
            response = 'Did you mean {} or {}?'.format(
                results[0].full_name, results[1].full_name)
        elif len(results) > 2:
            response = '{} results for {}.  Please be more specific.'.format(
                len(results), mep_name)
        self.conn.say(response, data.to)
        
    
    def get_mep_data(self, from_web=None):
        """Returns MEPList, either constructed from raw data fetched from web
        or pre-existing MEPList (if less than a day old)."""
        if from_web is None:
            from_web = not (datetime.date.today() == self.xml_date)
        if from_web:
            xml_data = self.get_meps_from_web()
            xml_date = datetime.date.today()
        else:
            xml_data = self.xml_data
            xml_date = self.xml_date
        return MEPList(xml_data), xml_date
            
    
    def get_meps_from_web(self):
        """Returns raw XML data fetched from web."""
        data = urlopen(self.XML_URL)
        tree = ET.parse(data)
        root = tree.getroot()
        return root
    

