"""Placeholder entry point for the final interactive application."""


def main() -> None:
    try:
        import streamlit as st
    except ImportError as exc:
        raise RuntimeError('Install the app dependencies with: pip install -e ".[app]"') from exc

    st.set_page_config(page_title="Ocean Carbon Sampling", layout="wide")
    st.title("Ocean Carbon Sampling")
    st.info("The interactive application will be enabled after experiment results are frozen.")


if __name__ == "__main__":
    main()

