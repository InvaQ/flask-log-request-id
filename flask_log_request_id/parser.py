from flask import request

def amazon_elb_trace_id():
    """
    Extract the Amazon ELB trace ID from the Flask request headers.
    """
    amazon_request_id = request.headers.get('X-Amzn-Trace-Id', '')
    trace_id_params = dict(x.split('=') if '=' in x else (x, None) for x in amazon_request_id.split(';'))
    return trace_id_params.get('Self') or trace_id_params.get('Root')

def generic_http_header_parser_for(header_name):
    """
    Factory function to create a parser for a specific HTTP header.
    """
    def parser():
        return request.headers.get(header_name, '').strip() or None
    return parser

def x_request_id():
    """
    Parser for the X-Request-ID header.
    """
    return generic_http_header_parser_for('X-Request-ID')()

def x_correlation_id():
    """
    Parser for the X-Correlation-ID header.
    """
    return generic_http_header_parser_for('X-Correlation-ID')()

def auto_parser(parsers=(x_request_id, x_correlation_id, amazon_elb_trace_id)):
    """
    Try each parser in the list until a request ID is found.
    """
    for parser in parsers:
        request_id = parser()
        if request_id:
            return request_id
    return None