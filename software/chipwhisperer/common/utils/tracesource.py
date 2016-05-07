#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013-2014, NewAE Technology Inc
# All rights reserved.
#
# Author: Colin O'Flynn
#
# Find this and more at newae.com - this file is part of the chipwhisperer
# project, http://www.assembla.com/spaces/chipwhisperer
#
#    This file is part of chipwhisperer.
#
#    chipwhisperer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    chipwhisperer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with chipwhisperer.  If not, see <http://www.gnu.org/licenses/>.
#=================================================

from chipwhisperer.common.utils import util
from chipwhisperer.common.utils.parameters import Parameterized


class TraceSource(object):
    """
    It has traces as output
    Keeps a dictionary with all the registered objets and emits a signal when a new one is added
    """
    registeredObjects = util.DictType()
    sigRegisteredObjectsChanged = util.Signal()

    def __init__(self, name="Unknown"):
        self.sigTracesChanged = util.Signal()
        self.name = name

    def getTrace(self, n):
        return None

    def numPoints(self):
        return 0

    def numTraces(self):
        return 0

    def offset(self):
        return 0

    def register(self):
        self.registeredObjects[self.name] = self
        self.sigRegisteredObjectsChanged.emit()
        return self

    @classmethod
    def deregister(cls, name):
        if cls.registeredObjects.pop(name, None):
            cls.sigRegisteredObjectsChanged.emit()


class LiveTraceSource(TraceSource):
    """ It has live traces as output """

    def __init__(self, scope=None, name="Scope"):
        TraceSource.__init__(self, name)
        self._scope = None
        self.setScope(scope)
        self._lastData = []
        self._lastOffset = 0

    def setScope(self, newScope):
        if self._scope:
            self._scope.dataUpdated.disconnect(self.newScopeData)
        if newScope:
            newScope.dataUpdated.connect(self.newScopeData)
        self._scope = newScope

    def newScopeData(self, data=None, offset=0):
        self._lastData = data
        self._lastOffset = offset
        self.sigTracesChanged.emit()

    def getTrace(self, n):
        return self._lastData

    def numPoints(self):
        return len(self._lastData)

    def numTraces(self):
        return 1

    def offset(self):
        return self._lastOffset


class PassiveTraceObserver(Parameterized):
    """ It processes data from a TraceSource when requested """

    def __init__(self, parentParam=None):
        Parameterized.__init__(self, parentParam)
        self._traceSource = None
        self.params.addChildren([
            {'name':'Input', 'key':'input', 'type':'list', 'values':TraceSource.registeredObjects, 'set':self._setTraceSource}
        ])

    def setTraceSource(self, traceSource):
        par = self.findParam('input')
        par.setValue(traceSource)
        assert self._traceSource == traceSource

    def _setTraceSource(self, traceSource):
        self._traceSource = traceSource

    def traceSource(self):
        return self._traceSource

    def processTraces(self):
        pass

    def traceSourcesChanged(self):
        par = self.findParam('input')
        par.setLimits({})  # Will not update if the obj is the same :(
        par.setLimits(TraceSource.registeredObjects)


class ActiveTraceObserver(PassiveTraceObserver):
    """ It observes a TraceSource for state changes and process the Traces actively """

    def _setTraceSource(self, newTraceSource):
        if self._traceSource:
            self._traceSource.sigTracesChanged.disconnect(self.processTraces)
        if newTraceSource:
            newTraceSource.sigTracesChanged.connect(self.processTraces)
        self._traceSource = newTraceSource
        self.processTraces()