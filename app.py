import streamlit as st
import base64
from io import BytesIO
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import requests
import numpy as np
import cv2
import os

def mask_to_image(mask_data):
    if mask_data is not None:
        mask = (mask_data[:, :, -1] > 0).astype(np.uint8) * 255
        return Image.fromarray(mask)
    return None

def base64_to_image(base64_string):
    if base64_string.startswith('data:image'):
        base64_string = base64_string.split(',')[1]
    image_data = base64.b64decode(base64_string)
    image = Image.open(BytesIO(image_data))
    return image

def fetch_and_resize_image(source, max_size=512):
    if source.startswith('http'):
        response = requests.get(source)
        image = Image.open(BytesIO(response.content)).convert("RGB")
    else:
        image = base64_to_image(source).convert("RGB")
    
    width, height = image.size
    if max(width, height) > max_size:
        ratio = max_size / max(width, height)
        image = image.resize((int(width * ratio), int(height * ratio)), Image.LANCZOS)
    return image

def main():
    st.set_page_config(page_title="Image Canvas", layout="wide")

    query_params = st.query_params
    base_url = query_params.get("base_url", "")
    reference_url = query_params.get("reference_url", "")
    email = query_params.get("email", "")

    if not base_url or not reference_url:
        st.error("No image URL provided in query parameters.")
        return
    
    if "base_canvas_key" not in st.session_state:
        st.session_state.base_canvas_key = "initial_base_canvas"

    if "base_canvas_reset_counter" not in st.session_state:
        st.session_state.base_canvas_reset_counter = 0

    if 'base_image' not in st.session_state:
        st.session_state.base_image = fetch_and_resize_image(base_url)
        st.session_state.reference_image = fetch_and_resize_image(reference_url)

    if "ref_canvas_key" not in st.session_state:
        st.session_state.ref_canvas_key = "initial_ref_canvas"

    if "ref_canvas_reset_counter" not in st.session_state:
        st.session_state.ref_canvas_reset_counter = 0

    st.header("Image Canvas")

    clone_mask = st.checkbox("Clone Reference Mask to Background", False)

  
    with st.sidebar:
        st.header("Editing Tools")
        
        st.subheader("Tool Settings")
        drawing_mode = st.selectbox("Drawing tool:", ("freedraw", "line", "rect", "circle", "transform", "polygon"), key="drawing_mode")
        stroke_width = st.slider("Stroke width:", 1, 150, 75, key="stroke_width")
        stroke_color = st.color_picker("Stroke color:", "#B5B5B5", key="stroke_color")

    tab1, tab2, tab3 = st.tabs(["Base Image", "Reference Image", "View Masks"])

    with tab1:
         if st.session_state.base_image is not None:
            if st.button("Reset Base Canvas"):
                st.session_state.base_canvas_reset_counter += 1
                st.session_state.base_canvas_key = f"base_canvas_{st.session_state.base_canvas_reset_counter}"
                if "base_mask" in st.session_state:
                    del st.session_state["base_mask"]
                st.rerun()
            
          
            initial_drawing = None
            if clone_mask and "ref_mask" in st.session_state:
                resized_mask = cv2.resize(st.session_state["ref_mask"], (st.session_state.base_image.width, st.session_state.base_image.height), interpolation=cv2.INTER_NEAREST)
                initial_drawing = {
                    "version": "4.4.0",
                    "objects": [{
                        "type": "image",
                        "version": "4.4.0",
                        "originX": "left",
                        "originY": "top",
                        "left": 0,
                        "top": 0,
                        "width": st.session_state.base_image.width,
                        "height": st.session_state.base_image.height,
                        "fill": "rgb(0,0,0)",
                        "stroke": None,
                        "strokeWidth": 0,
                        "strokeDashArray": None,
                        "strokeLineCap": "butt",
                        "strokeDashOffset": 0,
                        "strokeLineJoin": "miter",
                        "strokeUniform": False,
                        "strokeMiterLimit": 4,
                        "scaleX": 1,
                        "scaleY": 1,
                        "angle": 0,
                        "flipX": False,
                        "flipY": False,
                        "opacity": 1,
                        "shadow": None,
                        "visible": True,
                        "backgroundColor": "",
                        "fillRule": "nonzero",
                        "paintFirst": "fill",
                        "globalCompositeOperation": "source-over",
                        "skewX": 0,
                        "skewY": 0,
                        "cropX": 0,
                        "cropY": 0,
                        "src": f"data:image/png;base64,{base64.b64encode(cv2.imencode('.png', resized_mask)[1]).decode()}",
                        "crossOrigin": None,
                        "filters": []
                    }]
                }
            
            base_mask = st_canvas(
                fill_color="rgba(181, 181, 181, 0.8)",
                stroke_width=stroke_width,
                stroke_color=f"{stroke_color}80",
                background_image=st.session_state.base_image,
                height=st.session_state.base_image.height,
                width=st.session_state.base_image.width,
                drawing_mode=drawing_mode,
                key=st.session_state.base_canvas_key,
                initial_drawing=initial_drawing
            )
            
            if base_mask.image_data is not None:
                st.session_state["base_mask"] = base_mask.image_data

    with tab2:
        if st.session_state.reference_image is not None:
            if st.button("Reset Reference Canvas"):
                st.session_state.ref_canvas_reset_counter += 1
                st.session_state.ref_canvas_key = f"ref_canvas_{st.session_state.ref_canvas_reset_counter}"
                if "ref_mask" in st.session_state:
                    del st.session_state["ref_mask"]
                st.rerun()

            ref_mask = st_canvas(
                fill_color="rgba(181, 181, 181, 0.8)",
                stroke_width=stroke_width,
                stroke_color=f"{stroke_color}80",
                background_image=st.session_state.reference_image,
                height=st.session_state.reference_image.height,
                width=st.session_state.reference_image.width,
                drawing_mode=drawing_mode,
                key=st.session_state.ref_canvas_key,
            )

            if ref_mask.image_data is not None:
                st.session_state["ref_mask"] = ref_mask.image_data

    with tab3:
        st.header("View Masks")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Base Image Mask")
            if "base_mask" in st.session_state:
                base_mask_image = mask_to_image(st.session_state["base_mask"])
                if base_mask_image:
                    base_image_rgba = st.session_state.base_image.convert("RGBA")
                    overlay = Image.new("RGBA", base_image_rgba.size, (255, 255, 255, 0))
                    mask = base_mask_image.convert("L")
                    overlay.paste((255, 0, 0, 128), (0, 0), mask)
                    combined = Image.alpha_composite(base_image_rgba, overlay)
                    st.image(combined, caption='Base Image with Mask', use_column_width=True)
            else:
                st.write("No mask created for the base image yet.")
        
        with col2:
            st.subheader("Reference Image Mask")
            if "ref_mask" in st.session_state:
                ref_mask_image = mask_to_image(st.session_state["ref_mask"])
                if ref_mask_image:
                    ref_image_rgba = st.session_state.reference_image.convert("RGBA")
                    overlay = Image.new("RGBA", ref_image_rgba.size, (255, 255, 255, 0))
                    mask = ref_mask_image.convert("L")
                    overlay.paste((255, 0, 0, 128), (0, 0), mask)
                    combined = Image.alpha_composite(ref_image_rgba, overlay)
                    st.image(combined, caption='Reference Image with Mask', use_column_width=True)
            else:
                st.write("No mask created for the reference image yet.")

        if st.button("Confirm All Data"):
            if "base_mask" in st.session_state and "ref_mask" in st.session_state:
                base_mask = (st.session_state["base_mask"][:, :, -1] > 0).astype(np.uint8) * 255
                ref_mask = (st.session_state["ref_mask"][:, :, -1] > 0).astype(np.uint8) * 255

                buffered_base = BytesIO()
                Image.fromarray(base_mask).save(buffered_base, format="PNG")
                base64_base = base64.b64encode(buffered_base.getvalue()).decode()

                buffered_ref = BytesIO()
                Image.fromarray(ref_mask).save(buffered_ref, format="PNG")
                base64_ref = base64.b64encode(buffered_ref.getvalue()).decode()

                response = requests.post(
                    os.getenv('BACKEND_URL'),
                    json={
                        "base_image": base_url,
                        "reference_image": reference_url,
                        "base_mask": base64_base,
                        "reference_mask": base64_ref,
                        "email": email
                    }
                )

                st.write("Success" if response.status_code == 200 else "Failed to send data")
            else:
                st.error("Both masks are required to be drawn before uploading.")

if __name__ == "__main__":
    main()
