import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface UIState {
  sidebarCollapsed: boolean;
  globalSearchVisible: boolean;
  activeModal: string | null;
  activeModalProps: Record<string, unknown>;
}

const initialState: UIState = {
  sidebarCollapsed: false,
  globalSearchVisible: false,
  activeModal: null,
  activeModalProps: {},
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleSidebar(state) {
      state.sidebarCollapsed = !state.sidebarCollapsed;
    },
    setSidebarCollapsed(state, action: PayloadAction<boolean>) {
      state.sidebarCollapsed = action.payload;
    },
    toggleGlobalSearch(state) {
      state.globalSearchVisible = !state.globalSearchVisible;
    },
    setGlobalSearchVisible(state, action: PayloadAction<boolean>) {
      state.globalSearchVisible = action.payload;
    },
    openModal(state, action: PayloadAction<{ modal: string; props?: Record<string, unknown> }>) {
      state.activeModal = action.payload.modal;
      state.activeModalProps = action.payload.props || {};
    },
    closeModal(state) {
      state.activeModal = null;
      state.activeModalProps = {};
    },
  },
});

export const {
  toggleSidebar,
  setSidebarCollapsed,
  toggleGlobalSearch,
  setGlobalSearchVisible,
  openModal,
  closeModal,
} = uiSlice.actions;
export default uiSlice.reducer;
