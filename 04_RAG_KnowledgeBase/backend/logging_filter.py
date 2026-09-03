import logging
from logging_context import request_id_context


class RequestIdFilter(logging.Filter):

    def filter(self, record):
        record.request_id = request_id_context.get()
        return True