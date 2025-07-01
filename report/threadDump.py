from collections import defaultdict
import streamlit as st
import plotly.express as px
import pandas as pd
from data import cache

def get_blocked_info(thread_states, thread_waiting_on, lock_owners, stack_map):
    blocked_info = []
    method_counts = defaultdict(int)
    for thread_name, lock in thread_waiting_on.items():
        if thread_states.get(thread_name) == "BLOCKED":
            blocking_thread = lock_owners.get(lock, "Unknown")
            blocked_stack = stack_map.get(thread_name, "N/A")
            blocking_stack = stack_map.get(blocking_thread, "N/A")
            blocked_info.append({
                "Blocked Thread": thread_name,
                "Waiting on Lock": lock,
                "Blocked Stack": blocked_stack,
                "Blocking Thread": blocking_thread,
                "Blocking Stack": blocking_stack
            })
            method_counts[blocked_stack] += 1
    return blocked_info, method_counts

def show_blocking_relationships_table(blocked_info):
    st.subheader("Blocking Relationships Table")
    st.dataframe(blocked_info, use_container_width=True)

def show_automated_observations(blocked_info):
    st.subheader("\U0001F50D Automated Observations")
    if any("WorkCalendar.checkDate" in row["Blocked Stack"] for row in blocked_info):
        st.error("High contention detected on WorkCalendar.checkDate. Consider reducing synchronized blocks or refactoring this logic.")
    if any("WebappClassLoaderBase.getResource" in row["Blocked Stack"] for row in blocked_info):
        st.warning("Classloader contention detected. Multiple threads are stuck accessing class/resource loaders. Consider optimizing dynamic loading or disabling TLD scanning.")
    if any("getArchiveEntry" in row["Blocked Stack"] for row in blocked_info):
        st.info("Potential bottleneck in archive resource access. Investigate disk I/O or JAR scanning configuration.")

def show_hotspot_methods(method_counts):
    st.subheader("\U0001F525 Top Hotspot Methods")
    hotspot_table = sorted(method_counts.items(), key=lambda x: x[1], reverse=True)
    for method, count in hotspot_table[:5]:
        st.write(f"{method} - {count} BLOCKED threads")
    return hotspot_table

def show_blocking_relationship_graph(blocked_info):
    st.subheader("\U0001F4CA Blocking Relationship Graph")
    if blocked_info:
        df_graph = pd.DataFrame(blocked_info)
        fig = px.sunburst(
            df_graph,
            path=['Blocking Thread', 'Blocked Thread'],
            values=None,
            title="Thread Blocking Hierarchy",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig, use_container_width=True)

        fig_bar = px.bar(
            df_graph.groupby("Blocking Thread").size().reset_index(name='Blocked Count'),
            x='Blocking Thread',
            y='Blocked Count',
            title="Top Blocking Threads",
            color='Blocked Count',
            color_continuous_scale='Tealgrn'
        )
        st.plotly_chart(fig_bar, use_container_width=True)

def show_blocking_method_deep_dive(hotspot_table, full_stack_map, thread_states):
    st.subheader("\U0001F50E Detailed Thread Dump for a Specific Method")
    # Only allow non-None, non-empty method names in the selectbox
    method_options = [m for m, _ in hotspot_table if isinstance(m, str) and m]
    if not method_options:
        st.info("No valid methods found for deep dive.")
        return
    method_filter = st.selectbox("Select a method to drill down", method_options)
    matching_threads = []

    for thread_name, stack in full_stack_map.items():
        # Ensure stack is a list before iterating and frame is a string
        if isinstance(stack, list) and any(isinstance(frame, str) and method_filter in frame for frame in stack):
            full_trace = "\n".join([frame for frame in stack if isinstance(frame, str)])
            matching_threads.append({
                "Thread Name": thread_name,
                "Thread State": thread_states.get(thread_name, "UNKNOWN"),
                "Stack Trace": full_trace
            })

    if matching_threads:
        st.write(f"{len(matching_threads)} thread(s) matched method '{method_filter}'")
        for thread in matching_threads:
            with st.expander(f"🔹 {thread['Thread Name']} ({thread['Thread State']})"):
                st.code(thread["Stack Trace"], language="text")
    else:
        st.info("No threads matched the selected method.")

def show_thread_states_summary(thread_states):
    import pandas as pd
    st.markdown("### Thread States Summary")
    state_counts = pd.Series(thread_states).value_counts().reset_index()
    state_counts.columns = ["State", "Count"]
    st.dataframe(state_counts)

def show_thread_group_summary(thread_states):
    import pandas as pd
    st.markdown("### Thread Group Summary")
    group_counts = {}
    for name in thread_states:
        group = name.split('-')[0] if '-' in name else name
        group_counts[group] = group_counts.get(group, 0) + 1
    df = pd.DataFrame(list(group_counts.items()), columns=["Thread Group", "Count"])
    df = df.sort_values("Count", ascending=False).reset_index(drop=True)
    # Pad the count column for visual centering (optional)
    df["Count"] = df["Count"].astype(str).str.center(30)
    st.dataframe(df, use_container_width=True)
    # st.dataframe(df.style.set_properties(subset=["Count"], **{'text-align': 'center'}), use_container_width=True)


def show_threads_by_state(thread_states, full_stack_map):
    """
    Displays a filter for all thread states and, based on the selected filter,
    shows all threads in that state with their stack traces.
    """
    st.markdown("### 🔎 Explore Threads by State")
    # Get unique states and sort for UI
    unique_states = sorted(set(thread_states.values()))
    if not unique_states:
        st.info("No thread states found.")
        return

    selected_state = st.selectbox("Select a thread state to view all threads in that state:", unique_states)
    state_map = cache.get_threads_by_state(thread_states, full_stack_map)
    threads_in_state = state_map.get(selected_state, [])

    st.write(f"Found {len(threads_in_state)} thread(s) in state **{selected_state}**.")
    if not threads_in_state:
        st.info("No threads found in the selected state.")
        return

    for thread_name, stack_str in threads_in_state:
        with st.expander(f"🔹 {thread_name}"):
            st.code(stack_str, language="text")


def detect_deadlocks(thread_waiting_on, lock_owners):
    # Build wait-for graph
    wait_for = {}
    for thread, lock in thread_waiting_on.items():
        owner = lock_owners.get(lock)
        if owner:
            wait_for[thread] = owner
    # Detect cycles
    visited = set()
    for start in wait_for:
        path = set()
        t = start
        while t in wait_for and t not in path:
            path.add(t)
            t = wait_for[t]
        if t == start:
            # Prepare a summary string for the dashboard
            summary = (
                f"**Deadlock detected involving the following threads:**\n\n"
                + "\n".join(f"- {thread}" for thread in path)
            )
            st.error(summary)
            return True, path
    st.success("No deadlocks detected in this thread dump.")
    return False, None




# # Main function to display the thread dump dashboard
def show_thread_dump_dashboard(thread_states, thread_waiting_on, lock_owners, stack_map, full_stack_map):
    show_thread_states_summary(thread_states=thread_states)
    show_thread_group_summary(thread_states=thread_states)

    blocked_info, method_counts = get_blocked_info(thread_states, thread_waiting_on, lock_owners, stack_map)
    detect_deadlocks(thread_waiting_on, lock_owners)
    show_blocking_relationships_table(blocked_info)
    show_automated_observations(blocked_info)
    hotspot_table = show_hotspot_methods(method_counts)
    show_blocking_relationship_graph(blocked_info)
    show_blocking_method_deep_dive(hotspot_table, full_stack_map, thread_states)
    show_threads_by_state(thread_states=thread_states, full_stack_map=full_stack_map)
