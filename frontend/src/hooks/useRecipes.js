/**
 * Custom hook for all Recipe API interactions.
 * Encapsulates loading, error, and data state management.
 */

import { useState, useCallback } from 'react';
import client from '../api/client';

export function useRecipes() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /** Extract a recipe from a URL */
  const extractRecipe = useCallback(async (url) => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await client.post('/recipes/extract', { url });
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /** Fetch paginated recipe list */
  const fetchRecipes = useCallback(async (page = 1, perPage = 10) => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await client.get('/recipes/', {
        params: { page, per_page: perPage },
      });
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /** Fetch a single recipe by ID */
  const fetchRecipe = useCallback(async (id) => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await client.get(`/recipes/${id}`);
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /** Delete a recipe by ID */
  const deleteRecipe = useCallback(async (id) => {
    setError(null);
    try {
      await client.delete(`/recipes/${id}`);
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  /** Generate a meal plan from multiple recipe IDs */
  const generateMealPlan = useCallback(async (recipeIds) => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await client.post('/recipes/meal-plan', {
        recipe_ids: recipeIds,
      });
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    loading,
    error,
    setError,
    extractRecipe,
    fetchRecipes,
    fetchRecipe,
    deleteRecipe,
    generateMealPlan,
  };
}
