"""Reusable file uploader components with clean status feedback."""

import streamlit as st
from typing import Optional, List, Any
from utils.constants import ALLOWED_RESUME_EXTENSIONS


def render_resume_uploader(key: str = "resume_uploader") -> Optional[Any]:
    """Render a clean resume file uploader with supported format badges and accurate limits."""
    st.markdown(
        '<div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.5rem; font-weight: 500;">'
        'Supported Formats: PDF, DOCX, TXT • Maximum File Size: 10 MB'
        '</div>',
        unsafe_allow_html=True
    )
    
    uploaded_file = st.file_uploader(
        label="Upload resume file",
        type=ALLOWED_RESUME_EXTENSIONS,
        key=key,
        label_visibility="collapsed"
    )
    
    if uploaded_file is not None:
        file_size_kb = len(uploaded_file.getvalue()) / 1024
        st.markdown(
            f'<div style="display: flex; align-items: center; justify-content: space-between; background-color: var(--bg-surface-alt); border: 1px solid var(--border-subtle); padding: 8px 12px; border-radius: 6px; margin-top: 8px;">'
            f'<div style="display: flex; align-items: center; gap: 8px;">'
            f'<span style="font-size: 0.85rem; font-weight: 600; color: var(--text-primary);">📄 {uploaded_file.name}</span>'
            f'<span style="font-size: 0.75rem; color: var(--text-muted);">({file_size_kb:.1f} KB)</span>'
            f'</div>'
            f'<span class="tf-tag tf-tag-matched" style="font-size: 0.75rem;">✓ Resume Ready</span>'
            f'</div>',
            unsafe_allow_html=True
        )
        
    return uploaded_file


def render_batch_uploader(key: str = "batch_resumes_uploader") -> List[Any]:
    """Render a multi-file resume uploader for Recruiter batch screening."""
    st.markdown(
        '<div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.5rem; font-weight: 500;">'
        'Supported Formats: PDF, DOCX, TXT • Maximum File Size: 10 MB per file'
        '</div>',
        unsafe_allow_html=True
    )
    
    uploaded_files = st.file_uploader(
        label="Upload multiple candidate resumes",
        type=ALLOWED_RESUME_EXTENSIONS,
        accept_multiple_files=True,
        key=key,
        label_visibility="collapsed"
    )
    
    if uploaded_files:
        st.markdown(
            f'<div style="margin-top: 10px; margin-bottom: 6px; font-size: 0.85rem; font-weight: 600; color: var(--text-primary);">'
            f'Uploaded Resumes ({len(uploaded_files)} files ready for screening):'
            f'</div>',
            unsafe_allow_html=True
        )
        
        file_items_html = "".join([
            f'<div style="display: flex; align-items: center; justify-content: space-between; background-color: var(--bg-surface-alt); border: 1px solid var(--border-subtle); padding: 6px 10px; border-radius: 4px; margin-bottom: 4px;">'
            f'<div style="display: flex; align-items: center; gap: 6px;">'
            f'<span style="font-size: 0.8rem; color: var(--text-primary); font-weight: 500;">📄 {f.name}</span>'
            f'<span style="font-size: 0.72rem; color: var(--text-muted);">({len(f.getvalue()) / 1024:.1f} KB)</span>'
            f'</div>'
            f'<span class="tf-tag tf-tag-matched" style="font-size: 0.7rem; padding: 2px 6px;">✓ Ready</span>'
            f'</div>'
            for f in uploaded_files
        ])
        st.markdown(f'<div style="max-height: 180px; overflow-y: auto; margin-bottom: 10px;">{file_items_html}</div>', unsafe_allow_html=True)
        
    return uploaded_files or []
