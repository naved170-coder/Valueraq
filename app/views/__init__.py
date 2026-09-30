"""Shared view helpers."""
from flask import g, render_template

from .. import schema, seo


def render_page(template, meta: seo.PageMeta, allow_params=(), status=200, **ctx):
    seo.finalize(meta, allow_params=allow_params)
    if not meta.indexable:
        g.robots_header = meta.robots
    crumbs = [("Home", "/")] + list(meta.breadcrumbs)
    nodes = [schema.organization(), schema.website()]
    if meta.breadcrumbs:
        nodes.append(schema.breadcrumb_list(crumbs))
    nodes.extend(meta.schema)
    g.page_meta = meta
    html = render_template(template, meta=meta, crumbs=crumbs, jsonld=schema.graph(nodes), **ctx)
    return html, status
