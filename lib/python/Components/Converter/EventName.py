from Components.Converter.Converter import Converter
from Components.Element import cached
from Components.Converter.genre import getGenreStringSub
from Components.config import config
from Components.UsageConfig import dropEPGNewLines, replaceEPGSeparator
from time import time, localtime


class EventName(Converter):
	NAME = 0
	SHORT_DESCRIPTION = 1
	EXTENDED_DESCRIPTION = 2
	FULL_DESCRIPTION = 3
	ID = 4
	NAME_NOW = 5
	NAME_NEXT = 6
	GENRE = 7
	RATING = 8
	SRATING = 9
	PDC = 10
	PDCTIME = 11
	PDCTIMESHORT = 12
	ISRUNNINGSTATUS = 13
	FORMAT_STRING = 14
	RAWRATING = 15

	def __init__(self, type):
		Converter.__init__(self, type)
		self.parts = [(arg.strip() if i else arg) for i, arg in enumerate(type.split(","))]
		if len(self.parts) > 1:
			self.type = self.FORMAT_STRING
			self.separator = self.parts[0]
		else:
			if type == "Description":
				self.type = self.SHORT_DESCRIPTION
			elif type == "ExtendedDescription":
				self.type = self.EXTENDED_DESCRIPTION
			elif type == "FullDescription":
				self.type = self.FULL_DESCRIPTION
			elif type == "ID":
				self.type = self.ID
			elif type == "NameNow":
				self.type = self.NAME_NOW
			elif type == "NameNext":
				self.type = self.NAME_NEXT
			elif type == "Genre":
				self.type = self.GENRE
			elif type == "Rating":
				self.type = self.RATING
			elif type == "SmallRating":
				self.type = self.SRATING
			elif type == "Pdc":
				self.type = self.PDC
			elif type == "PdcTime":
				self.type = self.PDCTIME
			elif type == "PdcTimeShort":
				self.type = self.PDCTIMESHORT
			elif type == "IsRunningStatus":
				self.type = self.ISRUNNINGSTATUS
			elif type == "RawRating":
				self.type = self.RAWRATING
			else:
				self.type = self.NAME

	@cached
	def getBoolean(self):
		event = self.source.event
		if event is None:
			return False
		if self.type == self.NAME:
			return bool(self.getText())
		if self.type == self.PDC:
			if event.getPdcPil():
				return True
		return False

	boolean = property(getBoolean)

	@cached
	def getText(self):
		event = self.source.event
		if event is None:
			return ""

		if self.type == self.NAME:
			return event.getEventName()
		elif self.type == self.SRATING:
			rating = event.getParentalData()
			if rating is None:
				return ""
			else:
				country = rating.getCountryCode()
				age = rating.getRating()
				if age == 0:
					return _("All ages")
				elif age > 15:
					return _("bc%s") % age
				else:
					age += 3
					return " %d+" % age
		elif self.type == self.RATING:
			rating = event.getParentalData()
			if rating is None:
				return ""
			else:
				country = rating.getCountryCode()
				age = rating.getRating()
				if age == 0:
					return _("Rating undefined")
				elif age > 15:
					return _("Rating defined by broadcaster - %d") % age
				else:
					age += 3
					return _("Minimum age %d years") % age
		elif self.type == self.GENRE:
			genre = event.getGenreData()
			if genre is None:
				return ""
			else:
				return getGenreStringSub(genre.getLevel1(), genre.getLevel2())
		elif self.type == self.NAME_NOW:
			return pgettext("now/next: 'now' event label", "Now") + ": " + event.getEventName()
		elif self.type == self.NAME_NEXT:
			return pgettext("now/next: 'next' event label", "Next") + ": " + event.getEventName()
		elif self.type == self.SHORT_DESCRIPTION:
			return dropEPGNewLines(event.getShortDescription())
		elif self.type == self.EXTENDED_DESCRIPTION:
			return dropEPGNewLines(event.getExtendedDescription()) or dropEPGNewLines(event.getShortDescription())
		elif self.type == self.FULL_DESCRIPTION:
			description = dropEPGNewLines(event.getShortDescription())
			extended = dropEPGNewLines(event.getExtendedDescription().rstrip())
			if description and extended:
				if description.replace('\n', '') == extended.replace('\n', ''):
					return extended
				description += replaceEPGSeparator(config.epg.fulldescription_separator.value)
			return description + extended
		elif self.type == self.ID:
			return str(event.getEventId())
		elif self.type == self.PDC:
			if event.getPdcPil():
				return _("PDC")
			return ""
		elif self.type in (self.PDCTIME, self.PDCTIMESHORT):
			pil = event.getPdcPil()
			if pil:
				if self.type == self.PDCTIMESHORT:
					return _("%02d:%02d") % ((pil & 0x7C0) >> 6, (pil & 0x3F))
				return _("%d.%02d. %02d:%02d") % ((pil & 0xF8000) >> 15, (pil & 0x7800) >> 11, (pil & 0x7C0) >> 6, (pil & 0x3F))
			return ""
		elif self.type == self.ISRUNNINGSTATUS:
			if event.getPdcPil():
				running_status = event.getRunningStatus()
				if running_status == 1:
					return _("not running")
				if running_status == 2:
					return _("starts in a few seconds")
				if running_status == 3:
					return _("pausing")
				if running_status == 4:
					return _("running")
				if running_status == 5:
					return _("service off-air")
				if running_status in (6, 7):
					return _("reserved for future use")
				return _("undefined")
			return ""
		elif self.type == self.RAWRATING:
			rating = event.getParentalData()
			if rating:
				return "%d" % rating.getRating()
		elif self.type == self.FORMAT_STRING:
			begin = event.getBeginTime()
			end = begin + event.getDuration()
			now = int(time())
			t_start = localtime(begin)
			t_end = localtime(end)
			if begin <= now <= end:
				duration = end - now
				duration_str = "+%d min" % (duration / 60)
			else:
				duration = event.getDuration()
				duration_str = "%d min" % (duration / 60)
			start_time_str = "%2d:%02d" % (t_start.tm_hour, t_start.tm_min)
			end_time_str = "%2d:%02d" % (t_end.tm_hour, t_end.tm_min) 
			name = event.getEventName()
			res_str = ""
			for x in self.parts[1:]:
				if x == "NAME" and name:
					res_str = self.appendToStringWithSeparator(res_str, name)
				if x == "STARTTIME" and start_time_str:
					res_str = self.appendToStringWithSeparator(res_str, start_time_str)
				if x == "ENDTIME" and end_time_str:
					res_str = self.appendToStringWithSeparator(res_str, end_time_str)
				if x == "TIMERANGE" and start_time_str and end_time_str:
					res_str = self.appendToStringWithSeparator(res_str, "%s - %s" % (start_time_str, end_time_str))
				if x == "DURATION" and duration_str:
					res_str = self.appendToStringWithSeparator(res_str, duration_str)
			return res_str

	text = property(getText)
